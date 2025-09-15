import streamlit as st
import rdflib
from pathlib import Path
import pandas as pd

# Set page config
st.set_page_config(
    page_title="Ontology Search Interface",
    page_icon="🧠",
    layout="wide"
)

# Title
st.title("🧠 Ontology Search Interface")
st.markdown("Search and explore concepts, instances, and relationships in your ontology")

# Sidebar for ontology selection
st.sidebar.header("Ontology Management")

# File uploader for ontology
uploaded_file = st.sidebar.file_uploader(
    "Upload Ontology File", 
    type=['owl', 'rdf', 'ttl', 'n3', 'jsonld'],
    help="Upload your ontology file to begin searching"
)

# Initialize session state
if 'ontology' not in st.session_state:
    st.session_state.ontology = None
if 'loaded_file' not in st.session_state:
    st.session_state.loaded_file = None

# Load ontology function using rdflib
@st.cache_resource
def load_ontology_rdflib(file_path):
    try:
        g = rdflib.Graph()
        # Determine format based on file extension
        if file_path.endswith('.ttl'):
            g.parse(file_path, format="turtle")
        elif file_path.endswith('.rdf') or file_path.endswith('.xml'):
            g.parse(file_path, format="xml")
        elif file_path.endswith('.jsonld'):
            g.parse(file_path, format="json-ld")
        else:
            # Try to auto-detect
            g.parse(file_path)
        return g
    except Exception as e:
        st.error(f"Error loading ontology: {str(e)}")
        return None

# Handle file upload
if uploaded_file is not None and uploaded_file != st.session_state.loaded_file:
    # Save uploaded file temporarily
    temp_path = f"/tmp/{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Load ontology with rdflib
    st.session_state.ontology = load_ontology_rdflib(temp_path)
    st.session_state.loaded_file = uploaded_file
    st.session_state.uploaded_file_path = temp_path  # Store path for SPARQL queries
    
    if st.session_state.ontology:
        triple_count = len(st.session_state.ontology)
        st.sidebar.success(f"[OK] Loaded: {uploaded_file.name}")
        st.sidebar.info(f"Triples: {triple_count}")
    else:
        st.sidebar.error("[ERROR] Failed to load ontology")

# Main interface
if st.session_state.ontology:
    # Create tabs
    tab1, tab2 = st.tabs(["Search Fraud Activities", "Browse Ontology"])
    
    with tab1:
        st.header("Fraud Activity Search")
        st.markdown("Search for Federal Fraud Schemes related to specific fraud activities using advanced SPARQL queries.")
        
        # Fraud activity mapping: Display Label -> Class URI
        fraud_activity_mapping = {
            "Public Emergency Fraud": "public_emergency_fraud",
            "Identity Fraud": "IdentityFraud",
            "Healthcare Fraud": "HealthcareFraud", 
            "Tax Fraud": "TaxFraud",
            "Procurement Fraud": "ProcurementFraud",
            "Investment Fraud": "InvestmentFraud",
            "Wire Fraud": "WireFraud",
            "Mail Fraud": "MailFraud",
            "Financial Institution Fraud": "FinancialInstitutionFraud",
            "Corporate Fraud": "CorporateFraud",
            "Contract Fraud": "ContractFraud",
            "Grant Fraud": "GrantFraud",
            "Housing Fraud": "HousingFraud",
            "Insurance Fraud": "InsuranceFraud",
            "Loan Fraud": "LoanFraud",
            "Student Financial Aid Fraud": "StudentFinancialAidFraud",
            "Corruption": "Corruption",
            "Cyber Espionage": "CyberEspionage",
            "Cyberextortion": "Cyberextortion"
        }
        
        # Fraud activity selection
        fraud_activity_label = st.selectbox(
            "Select Fraud Activity Type:",
            options=list(fraud_activity_mapping.keys()),
            help="Choose a fraud activity type to find related Federal Fraud Schemes"
        )
        
        # Get the corresponding class URI
        fraud_activity = fraud_activity_mapping[fraud_activity_label] if fraud_activity_label else None
        
        if st.button("Search Fraud Schemes"):
            if fraud_activity_label and fraud_activity:
                # SPARQL query using the user's working approach
                sparql_query = f"""
                PREFIX gfo: <https://gaoinnovations.gov/antifraud_resource/howfraudworks/gfo/>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
                 
                SELECT DISTINCT ?individual ?individualName
                WHERE {{
                    ?individual a gfo:FederalFraudScheme ;
                                rdfs:label ?individualName .
                   
                    {{
                        # Path 1: Through involves property
                        ?individual a ?someClass .
                        ?someClass owl:onProperty gfo:involves ;
                                   owl:someValuesFrom ?specificFraud .
                       
                        ?specificFraud rdfs:subClassOf* ?fraudType .
                        ?fraudType rdfs:label ?fraudTypeName .
                       
                        ?specificFraud rdfs:subClassOf* gfo:{fraud_activity} .
                    }}
                    UNION
                    {{
                        # Path 2: Direct instance of subclass
                        ?individual a ?fraudSchemeClass .
                        ?fraudSchemeClass rdfs:subClassOf* gfo:{fraud_activity} .
                        ?fraudSchemeClass rdfs:subClassOf* ?fraudType .
                        ?fraudType rdfs:label ?fraudTypeName .
                       
                        FILTER(?fraudSchemeClass != gfo:FederalFraudScheme)
                    }}
                    
                    # Filter out the top-level FraudActivity class
                    FILTER(?fraudType != gfo:FraudActivity)
                }}
                ORDER BY ?individualName
                """
                
                try:
                    # Execute SPARQL query using rdflib
                    import rdflib
                    
                    # Create a new graph and load the ontology
                    g = rdflib.Graph()
                    
                    # Get the uploaded file path from session state
                    if 'uploaded_file_path' in st.session_state:
                        g.parse(st.session_state.uploaded_file_path)
                        
                        # Execute the query
                        results = list(g.query(sparql_query))
                        
                        if results:
                            st.success(f"[OK] Found {len(results)} Federal Fraud Schemes related to {fraud_activity_label}")
                            
                            # Display results in expandable cards
                            for i, row in enumerate(results):
                                scheme_name = str(row.individualName)
                                scheme_uri = str(row.individual)
                                
                                with st.expander(f"{i+1}. {scheme_name}"):
                                    st.write(f"**Full Name:** {scheme_name}")
                                    st.write(f"**URI:** {scheme_uri.split('/')[-1]}")
                                    st.write(f"**Related to:** {fraud_activity_label}")
                                    
                                    # Could add more details here if needed
                                    st.markdown("---")
                                    st.caption("Found using advanced SPARQL query with transitive closure")
                        else:
                            st.info(f"No Federal Fraud Schemes found for {fraud_activity_label}")
                            
                except Exception as e:
                    st.error(f"[ERROR] SPARQL query failed: {str(e)}")
                    st.info("Make sure your ontology file is properly loaded.")
            else:
                st.warning("Please select a fraud activity type.")
    
    with tab2:
        st.header("Browse Ontology Structure")
        
        if st.session_state.ontology:
            g = st.session_state.ontology
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Classes")
                # Get classes from RDF graph
                classes = []
                for s, p, o in g:
                    if str(p) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" and str(o) == "http://www.w3.org/2002/07/owl#Class":
                        class_name = str(s).split('/')[-1] if '/' in str(s) else str(s)
                        classes.append(class_name)
                
                classes_df = pd.DataFrame({"Class Name": sorted(list(set(classes)))})
                st.dataframe(classes_df, use_container_width=True)
            
            with col2:
                st.subheader("Properties")
                # Get properties from RDF graph
                properties = set()
                for s, p, o in g:
                    prop_name = str(p).split('/')[-1] if '/' in str(p) else str(p).split('#')[-1]
                    properties.add(prop_name)
                
                properties_df = pd.DataFrame({"Property": sorted(list(properties))})
                st.dataframe(properties_df, use_container_width=True)
            
            # Statistics
            st.subheader("Ontology Statistics")
            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
            
            with stats_col1:
                st.metric("Total Triples", len(g))
            with stats_col2:
                st.metric("Unique Subjects", len(set(g.subjects())))
            with stats_col3:
                st.metric("Unique Predicates", len(set(g.predicates())))
            with stats_col4:
                st.metric("Unique Objects", len(set(g.objects())))
        else:
            st.info("Please upload an ontology file first.")

else:
    st.info("Please upload an ontology file to begin")
    
    # Example section
    st.markdown("---")
    st.header("Getting Started")
    st.markdown("""
    **What this interface provides:**
    
    1. **Fraud Activity Search**: Find Federal Fraud Schemes using advanced SPARQL queries
    2. **Browse Tab**: Explore your ontology structure and statistics  
    
    **Supported formats**: OWL, RDF, TTL, N3, JSON-LD
    
    **Next steps**:
    - Upload your ontology file using the sidebar
    - Use the Fraud Activity Search to find related schemes
    - Use Jupyter Lab (accessible at http://localhost:8888) for advanced editing
    
    **How it works**:
    - Uses sophisticated SPARQL queries with transitive closure
    - Finds both direct and indirect relationships through class hierarchies
    - Captures complex OWL restrictions and property relationships
    """)