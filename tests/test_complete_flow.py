#!/usr/bin/env python3
"""
Complete End-to-End Test Script for Repository Analyzer

This script tests the complete flow:
1. Start the API server
2. Load a repository
3. Ingest the repository 
4. Perform searches
5. Validate results

Usage:
    python test_complete_flow.py
"""

import asyncio
import json
import logging
import os
import time
import requests
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RepoAnalyzerTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        

    def test_health(self) -> bool:
        """Test if the API is healthy and running"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Health check passed: {result}")
                return True
            else:
                logger.error(f"Health check failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Health check failed with exception: {e}")
            return False
    

    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        try:
            response = self.session.get(f"{self.base_url}/status")
            if response.status_code == 200:
                status = response.json()
                logger.info(f"System status: {status}")
                return status
            else:
                logger.error(f"Status check failed: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return {}
    

    def load_repository(self, owner: str, repo: str) -> bool:
        """Load a GitHub repository"""
        logger.info(f"Loading repository: {owner}/{repo}")
        
        try:
            params = {"repo_id": repo, "owner": owner}
            response = self.session.post(f"{self.base_url}/load_repo", params=params, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                if result["status"] == "success":
                    logger.info(f"Repository loaded successfully: {result}")
                    return True
                else:
                    logger.error(f"Repository loading failed: {result}")
                    return False
            else:
                logger.error(f"Repository loading failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Repository loading failed with exception: {e}")
            return False
    

    def ingest_repository(self) -> bool:
        """Ingest the loaded repository"""
        logger.info("Starting repository ingestion")
        
        try:
            response = self.session.post(f"{self.base_url}/ingest", timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                if result["status"] == "success":
                    logger.info(f"Repository ingested successfully: {result}")
                    return True
                else:
                    logger.error(f"Repository ingestion failed: {result}")
                    return False
            else:
                logger.error(f"Repository ingestion failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Repository ingestion failed with exception: {e}")
            return False
    

    def search_repository(self, query: str, file_path: str = None) -> Dict[str, Any]:
        """Search the repository"""
        logger.info(f"Searching repository with query: '{query}'")
        
        try:
            params = {"query": query}
            if file_path:
                params["file_path"] = file_path
                
            response = self.session.post(f"{self.base_url}/search", params=params, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if result["status"] == "success":
                    logger.info(f"Search completed successfully, found results: {result.get('results', [])}")
                    return result
                else:
                    logger.error(f"Search failed: {result}")
                    return {}
            else:
                logger.error(f"Search failed: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Search failed with exception: {e}")
            return {}
    

    def list_collections(self) -> Dict[str, Any]:
        """List Qdrant collections"""
        try:
            response = self.session.get(f"{self.base_url}/collections")
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Collections listed: {result}")
                return result
            else:
                logger.error(f"Failed to list collections: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return {}

def run_complete_test():
    """Run the complete test flow"""
    logger.info("=" * 50)
    logger.info("Starting Complete Repository Analyzer Test")
    logger.info("=" * 50)
    
    tester = RepoAnalyzerTester()
    
    logger.info("\n1. Testing API Health...")
    if not tester.test_health():
        logger.error("API health check failed. Make sure the server is running.")
        return False
    
    logger.info("\n2. Getting initial status...")
    initial_status = tester.get_status()
    
    
    logger.info("\n3. Loading test repository...")
    owner = "mevitts" 
    repo = "new-tracklist"
    
    if not tester.load_repository(owner, repo):
        logger.error("Failed to load repository")
        return False
    
    
    logger.info("\n4. Checking status after loading...")
    post_load_status = tester.get_status()
    
    
    logger.info("\n5. Ingesting repository...")
    if not tester.ingest_repository():
        logger.error("Failed to ingest repository")
        return False
    
    
    logger.info("\n6. Listing collections...")
    collections = tester.list_collections()
    
    logger.info("\n7. Performing searches...")
    
    search_queries = [
        "function definition",
        "class implementation", 
        "main method",
        "README",
        "import statement"
    ]
    
    search_results = []
    for query in search_queries:
        logger.info(f"Searching for: '{query}'")
        result = tester.search_repository(query)
        if result:
            search_results.append((query, result))
        time.sleep(1)

    logger.info("\n8. Final status check...")
    final_status = tester.get_status()
    
    logger.info("\n" + "=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Repository loaded: {owner}/{repo}")
    logger.info(f"Search queries tested: {len(search_queries)}")
    logger.info(f"Successful searches: {len(search_results)}")
    
    if search_results:
        logger.info("Search results preview:")
        for query, result in search_results[:3]:
            results_obj = result.get("results")
            if hasattr(results_obj, "points"):
                points = results_obj.points
            elif isinstance(results_obj, dict) and "points" in results_obj:
                points = results_obj["points"]
            elif isinstance(results_obj, list):
                points = results_obj
            else:
                points = []
            logger.info(f"  '{query}': {len(points)} results found")
            if points:
                logger.info(f"    Sample result: {points[0]}")
    
    logger.info("=" * 50)
    logger.info("Complete test flow finished successfully!")
    logger.info("=" * 50)
    
    return True

def check_requirements():
    """Check if required environment variables and dependencies are set"""
    logger.info("Checking requirements...")
    
    # Check environment variables
    required_env_vars = ["GITHUB_TOKEN"]
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        logger.info("You may need to set these for full functionality")
    
    # Check if Qdrant is accessible (basic check)
    try:
        import qdrant_client
        logger.info("Qdrant client library is available")
    except ImportError:
        logger.error("Qdrant client not installed. Run: pip install qdrant-client")
        return False
    
    return True

if __name__ == "__main__":
    if check_requirements():
        run_complete_test()
    else:
        logger.error("Requirements check failed")
