# ncbi_server.py
import httpx
import re
from mcp.server.fastmcp import FastMCP, Context

# Create an MCP server
mcp = FastMCP("NCBI Sequence Fetcher")

# Helper function for fetching from NCBI
async def fetch_from_ncbi(db: str, accession: str, rettype: str = "fasta") -> str:
    """Fetch data from NCBI using E-utilities"""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    # First, use esearch to get the ID for the accession
    async with httpx.AsyncClient() as client:
        search_url = f"{base_url}/esearch.fcgi?db={db}&term={accession}[accn]&retmode=json"
        search_response = await client.get(search_url)
        search_data = search_response.json()
        
        if not search_data.get("esearchresult", {}).get("idlist"):
            return f"No {db} record found for accession {accession}"
        
        id_list = search_data["esearchresult"]["idlist"]
        
        # Then use efetch to get the sequence data
        fetch_url = f"{base_url}/efetch.fcgi?db={db}&id={','.join(id_list)}&rettype={rettype}&retmode=text"
        fetch_response = await client.get(fetch_url)
        
        return fetch_response.text

@mcp.tool()
async def get_nucleotide_sequence(accession: str, ctx: Context) -> str:
    """Fetch nucleotide sequence from NCBI by accession number.
    
    Args:
        accession: NCBI nucleotide accession number (e.g., NM_000546, NG_005905)
    
    Returns:
        FASTA format sequence data
    """
    ctx.info(f"Fetching nucleotide sequence for accession: {accession}")
    return await fetch_from_ncbi("nucleotide", accession, "fasta")

@mcp.tool()
async def get_protein_sequence(accession: str, ctx: Context) -> str:
    """Fetch protein sequence from NCBI by accession number.
    
    Args:
        accession: NCBI protein accession number (e.g., NP_000537, P53_HUMAN)
    
    Returns:
        FASTA format protein sequence
    """
    ctx.info(f"Fetching protein sequence for accession: {accession}")
    return await fetch_from_ncbi("protein", accession, "fasta")

@mcp.tool()
async def get_sequence_metadata(accession: str, ctx: Context, db: str = "nucleotide") -> str:
    """Fetch metadata about a sequence from NCBI.
    
    Args:
        accession: NCBI accession number
        db: Database to search (nucleotide or protein)
    
    Returns:
        GenBank/GenPept format with detailed metadata
    """
    ctx.info(f"Fetching metadata for {db} accession: {accession}")
    return await fetch_from_ncbi(db, accession, "gb" if db == "nucleotide" else "gp")

@mcp.tool()
async def search_ncbi(query: str, ctx: Context, db: str = "nucleotide") -> str:
    """Search NCBI databases with a text query.
    
    Args:
        query: Search term (e.g., "BRCA1", "p53 tumor suppressor")
        db: Database to search (nucleotide, protein, gene, etc.)
    
    Returns:
        List of matching accession numbers and descriptions
    """
    ctx.info(f"Searching NCBI {db} database for: {query}")
    
    async with httpx.AsyncClient() as client:
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        search_url = f"{base_url}/esearch.fcgi?db={db}&term={query}&retmode=json&retmax=10"
        search_response = await client.get(search_url)
        search_data = search_response.json()
        
        if not search_data.get("esearchresult", {}).get("idlist"):
            return f"No results found for '{query}' in {db} database"
        
        id_list = search_data["esearchresult"]["idlist"]
        
        # Get summaries for the IDs
        summary_url = f"{base_url}/esummary.fcgi?db={db}&id={','.join(id_list)}&retmode=json"
        summary_response = await client.get(summary_url)
        summary_data = summary_response.json()
        
        results = []
        for id in id_list:
            try:
                doc_sum = summary_data["result"][id]
                accession = next((item["content"] for item in doc_sum.get("accessionversion", []) 
                                 if isinstance(item, dict) and "content" in item), "Unknown")
                if not accession or accession == "Unknown":
                    # Try to find accession in other fields
                    for field in ["caption", "title", "accession"]:
                        if field in doc_sum:
                            potential_acc = doc_sum[field]
                            if isinstance(potential_acc, str) and re.match(r'^[A-Z]{1,3}_?[0-9]+', potential_acc):
                                accession = potential_acc
                                break
                
                title = doc_sum.get("title", "No title available")
                results.append(f"ID: {id}, Accession: {accession}, Title: {title}")
            except Exception as e:
                results.append(f"Error processing ID {id}: {str(e)}")
        
        return "\n\n".join(results)

# Add a help tool to list available functionality
@mcp.tool()
def help() -> str:
    """Get help information about the NCBI Sequence Fetcher tools"""
    return """
NCBI Sequence Fetcher - Available Tools:

1. get_nucleotide_sequence(accession)
   Fetch nucleotide sequence from NCBI in FASTA format
   Example accessions: NM_000546, NG_005905, NC_000023

2. get_protein_sequence(accession)
   Fetch protein sequence from NCBI in FASTA format
   Example accessions: NP_000537, P53_HUMAN

3. get_sequence_metadata(accession, db="nucleotide")
   Get detailed metadata about a sequence in GenBank/GenPept format
   Databases: "nucleotide" or "protein"

4. search_ncbi(query, db="nucleotide")
   Search NCBI databases and get a list of matching entries
   Example queries: "BRCA1", "p53 tumor suppressor", "coronavirus spike"
   Databases: "nucleotide", "protein", "gene", etc.

Example usage:
- "Fetch the protein sequence for P53_HUMAN"
- "Get the nucleotide sequence for accession NM_000546"
- "Search NCBI for BRCA1 gene sequences"
- "Get detailed metadata for the TP53 gene"
"""