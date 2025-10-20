#!/usr/bin/env python3
"""
Storage Manager with Chroma/LanceDB integration and memory persistence
"""
import json
import os
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime


class MemoryPersistence:
    """Simple SQLite-based memory persistence"""
    
    def __init__(self, db_path: str = "workflow_memory.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Leads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT,
                contact_name TEXT,
                email TEXT UNIQUE,
                domain TEXT,
                role TEXT,
                linkedin TEXT,
                signal TEXT,
                score REAL,
                grade TEXT,
                technologies TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Campaigns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                leads_count INTEGER,
                config TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Email delivery log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_delivery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER,
                lead_email TEXT,
                provider TEXT,
                status TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                opened_at TIMESTAMP,
                clicked_at TIMESTAMP,
                replied_at TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
            )
        ''')
        
        # Feedback log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER,
                metric_type TEXT,
                metric_value REAL,
                recommendation TEXT,
                applied BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_leads(self, leads: List[Dict[str, Any]], campaign_name: str = None) -> int:
        """Store leads in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create campaign
        cursor.execute(
            "INSERT INTO campaigns (name, leads_count) VALUES (?, ?)",
            (campaign_name or f"Campaign_{datetime.now().strftime('%Y%m%d_%H%M')}", len(leads))
        )
        campaign_id = cursor.lastrowid
        
        # Store leads
        for lead in leads:
            cursor.execute('''
                INSERT OR REPLACE INTO leads 
                (company, contact_name, email, domain, role, linkedin, signal, score, grade, technologies)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lead.get("company", ""),
                lead.get("contact_name", ""),
                lead.get("email", ""),
                lead.get("domain", ""),
                lead.get("role", ""),
                lead.get("linkedin", ""),
                lead.get("signal", ""),
                lead.get("score", 0),
                lead.get("grade", ""),
                json.dumps(lead.get("technologies", []))
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Stored {len(leads)} leads in campaign {campaign_id}")
        return campaign_id
    
    def get_leads(self, limit: int = None, grade_filter: str = None) -> List[Dict[str, Any]]:
        """Retrieve leads from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM leads WHERE status = 'active'"
        params = []
        
        if grade_filter:
            query += " AND grade = ?"
            params.append(grade_filter)
        
        query += " ORDER BY score DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        leads = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return leads
    
    def log_email_delivery(self, campaign_id: int, lead_email: str, provider: str, status: str):
        """Log email delivery status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO email_delivery (campaign_id, lead_email, provider, status)
            VALUES (?, ?, ?, ?)
        ''', (campaign_id, lead_email, provider, status))
        
        conn.commit()
        conn.close()
    
    def get_campaign_stats(self, campaign_id: int) -> Dict[str, Any]:
        """Get campaign performance statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get email stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_sent,
                SUM(CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END) as opened,
                SUM(CASE WHEN clicked_at IS NOT NULL THEN 1 ELSE 0 END) as clicked,
                SUM(CASE WHEN replied_at IS NOT NULL THEN 1 ELSE 0 END) as replied
            FROM email_delivery 
            WHERE campaign_id = ?
        ''', (campaign_id,))
        
        stats = cursor.fetchone()
        conn.close()
        
        if stats:
            total_sent, opened, clicked, replied = stats
            return {
                "total_sent": total_sent,
                "opened": opened,
                "clicked": clicked,
                "replied": replied,
                "open_rate": round((opened / total_sent * 100), 2) if total_sent > 0 else 0,
                "click_rate": round((clicked / total_sent * 100), 2) if total_sent > 0 else 0,
                "reply_rate": round((replied / total_sent * 100), 2) if total_sent > 0 else 0
            }
        return {}


class ChromaVectorStore:
    """Chroma vector database integration (mock implementation)"""
    
    def __init__(self, collection_name: str = "leads_collection"):
        self.collection_name = collection_name
        self.vectors = []  # Mock storage
    
    def add_leads(self, leads: List[Dict[str, Any]]):
        """Add leads to vector store for similarity search"""
        for i, lead in enumerate(leads):
            # Create simple text embedding (mock)
            text = f"{lead.get('company', '')} {lead.get('role', '')} {lead.get('signal', '')}"
            vector_entry = {
                "id": f"lead_{i}",
                "text": text,
                "metadata": lead,
                "embedding": [hash(text) % 1000 / 1000.0]  # Mock embedding
            }
            self.vectors.append(vector_entry)
        
        print(f"✅ Added {len(leads)} leads to Chroma vector store")
    
    def search_similar(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar leads (mock implementation)"""
        # Simple text matching for demo
        results = []
        query_lower = query.lower()
        
        for vector in self.vectors:
            if query_lower in vector["text"].lower():
                results.append(vector["metadata"])
                if len(results) >= limit:
                    break
        
        return results


class StorageManager:
    """Main storage manager combining all storage backends"""
    
    def __init__(self):
        self.memory = MemoryPersistence()
        self.vector_store = ChromaVectorStore()
    
    def store_workflow_output(self, workflow_output: Dict[str, Any], campaign_name: str = None) -> int:
        """Store complete workflow output"""
        
        # Extract leads
        leads = []
        if "prospect_search" in workflow_output.get("results", {}):
            search_leads = workflow_output["results"]["prospect_search"].get("output", {}).get("leads", [])
            leads.extend(search_leads)
        
        if "scoring" in workflow_output.get("results", {}):
            scored_leads = workflow_output["results"]["scoring"].get("output", {}).get("ranked_leads", [])
            if scored_leads:
                leads = scored_leads
        
        # Store in SQLite
        campaign_id = self.memory.store_leads(leads, campaign_name)
        
        # Store in vector database
        self.vector_store.add_leads(leads)
        
        return campaign_id
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard/reporting"""
        
        # Get recent leads
        recent_leads = self.memory.get_leads(limit=20)
        
        # Get grade distribution
        a_leads = len(self.memory.get_leads(grade_filter="A"))
        b_leads = len(self.memory.get_leads(grade_filter="B"))
        c_leads = len(self.memory.get_leads(grade_filter="C"))
        d_leads = len(self.memory.get_leads(grade_filter="D"))
        
        return {
            "recent_leads": recent_leads[:10],  # Top 10
            "total_leads": len(recent_leads),
            "grade_distribution": {
                "A": a_leads, "B": b_leads, "C": c_leads, "D": d_leads
            },
            "top_companies": list(set(lead.get("company", "") for lead in recent_leads[:20])),
            "signals": list(set(lead.get("signal", "") for lead in recent_leads if lead.get("signal")))
        }


if __name__ == "__main__":
    # Demo storage functionality
    storage = StorageManager()
    
    # Mock workflow output for testing
    mock_output = {
        "results": {
            "prospect_search": {
                "output": {
                    "leads": [
                        {"company": "Test Corp", "contact_name": "John Doe", "email": "john@test.com", "score": 8.5, "grade": "A"},
                        {"company": "Demo Inc", "contact_name": "Jane Smith", "email": "jane@demo.com", "score": 6.2, "grade": "B"}
                    ]
                }
            }
        }
    }
    
    campaign_id = storage.store_workflow_output(mock_output, "Test Campaign")
    dashboard = storage.get_dashboard_data()
    
    print(f"📊 Dashboard data: {json.dumps(dashboard, indent=2)}")
