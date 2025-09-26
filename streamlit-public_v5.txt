import streamlit as st
import rdflib
from pathlib import Path
import pandas as pd
import os

# Set page config
st.set_page_config(
    page_title="US GAO Antifraud Resource Test Page",
    layout="wide"
)

# Title
st.title("US GAO Antifraud Resource Test Page")
st.markdown("Search and explore fraud concepts, instances, and relationships in the GAO's Conceptual Fraud Model")

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

# Auto-load default ontology function
def load_default_ontology():
    """Load GFO ontology from repository if available"""
    default_ontology_path = "gfo_turtle.ttl"
    
    if os.path.exists(default_ontology_path):
        try:
            with st.spinner("Loading GFO ontology from repository..."):
                st.session_state.ontology = load_ontology_rdflib(default_ontology_path)
                st.session_state.loaded_file = "gfo_turtle.ttl (default)"
                st.session_state.uploaded_file_path = default_ontology_path
                
                if st.session_state.ontology:
                    triple_count = len(st.session_state.ontology)
                    st.sidebar.success(f"[OK] Auto-loaded: gfo_turtle.ttl")
                    st.sidebar.info(f"Triples: {triple_count}")
                    return True
        except Exception as e:
            st.sidebar.error(f"[ERROR] Failed to auto-load default ontology: {str(e)}")
    return False

# Auto-load default ontology on first run
if st.session_state.ontology is None:
    load_default_ontology()

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
    st.header("Fraud Activity Search")
    st.markdown("Search for Federal Fraud Schemes related to specific fraud activities.")
    
    # Fraud activity mapping: Display Label -> Class URI
    fraud_activity_mapping = {
        "Beneficiary fraud": "BeneficiaryFraud",
        "Cellphone fraud": "CellphoneFraud",
        "Charity fraud": "CharityFraud",
        "Confidence fraud": "ConfidenceFraud",
        "Consumer fraud": "ConsumerFraud",
        "Corporate fraud": "CorporateFraud",
        "Corruption": "Corruption",
        "Cyber espionage": "CyberEspionage",
        "Cyberextortion": "Cyberextortion",
        "Environmental fraud": "EnvironmentalFraud",
        "Federal contract fraud": "ContractFraud",
        "Financial institution fraud": "FinancialInstitutionFraud",
        "Government furnished equipment fraud": "GovernmentFurnishedEquipmentFraud",
        "Grant fraud": "GrantFraud",
        "Healthcare fraud": "HealthcareFraud",
        "Housing fraud": "HousingFraud",
        "Identity fraud": "IdentityFraud",
        "Insurance fraud": "InsuranceFraud",
        "Investment fraud": "InvestmentFraud",
        "Laboratory fraud": "LaboratoryFraud",
        "Lien filing fraud": "LienFillingFraud",
        "Loan fraud": "LoanFraud",
        "Mail fraud": "MailFraud",
        "Media manipulation": "MediaManipulation",
        "Payment fraud": "PaymentFraud",
        "Procurement fraud": "ProcurementFraud",
        "Public assistance fraud": "AssistanceFraud",
        "Public emergency fraud": "public_emergency_fraud",
        "Sanction evasion fraud": "SanctionEvasion",
        "Student financial aid fraud": "StudentFinancialAidFraud",
        "Supervised release": "supervised_release",
        "Tax fraud": "TaxFraud",
        "Trafficking": "Trafficking",
        "Visa fraud": "VisaFraud",
        "Wire fraud": "WireFraud",
        "Workplace fraud": "WorkplaceFraud"
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
PREFIX dcterms: <http://purl.org/dc/terms/>
 
SELECT DISTINCT ?individual ?individualName ?description ?fraudNarrative ?isDefinedBy
WHERE {{
    ?individual a gfo:FederalFraudScheme ;
                rdfs:label ?individualName .
   
    # Get additional properties
    OPTIONAL {{ ?individual dcterms:description ?description . }}
    OPTIONAL {{ ?individual gfo:fraudNarrative ?fraudNarrative . }}
    OPTIONAL {{ ?individual rdfs:isDefinedBy ?isDefinedBy . }}
   
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
                            
                            # Extract the new properties (with fallbacks)
                            fraud_description = str(row.description) if row.description else "No description available"
                            fraud_narrative_uri = str(row.fraudNarrative) if row.fraudNarrative else "No fraud narrative available"
                            is_defined_by_url = str(row.isDefinedBy) if row.isDefinedBy else "No definition source available"
                            
                            with st.expander(f"{i+1}. {scheme_name}"):
                                st.write(f"**Fraud Description:** {fraud_description}")
                                
                                # Use st.text() for fraud narrative to avoid markdown interpretation of $ symbols
                                st.write("**Fraud Narrative:**")
                                st.text(fraud_narrative_uri)
                                
                                st.write(f"**Related to:** {fraud_activity_label}")
                                
                                # Could add more details here if needed
                                st.markdown("---")
                                st.caption(f"Source: {is_defined_by_url}")
                    else:
                        st.info(f"No Federal Fraud Schemes found for {fraud_activity_label}")
                        
            except Exception as e:
                st.error(f"[ERROR] SPARQL query failed: {str(e)}")
                st.info("Make sure your ontology file is properly loaded.")
        else:
            st.warning("Please select a fraud activity type.")

else:
    st.info("Please upload an ontology file to begin")
    
    # Example section
    st.markdown("---")
    st.header("Getting Started")
    st.markdown("""
    **What this interface provides:**
    
    1. **Fraud Activity Search**: Find Federal Fraud Schemes using SPARQL queries
    
    **Supported formats**: OWL, RDF, TTL, N3, JSON-LD
    
    **Next steps**:
    - Upload your ontology file using the sidebar
    - Use the Fraud Activity Search to find related fraud schemes
    
    **How it works**:
    - Finds both direct and indirect relationships through class hierarchies and property chains
    - Captures complex OWL restrictions and property relationships
    """)
