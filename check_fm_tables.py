#!/usr/bin/env python3
"""Check and create FM Global tables in Supabase."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_and_create_fm_tables():
    """Check if FM Global tables exist and create them if not."""
    
    # Get database URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found in .env")
        return
    
    try:
        # Connect to database
        conn = await asyncpg.connect(db_url)
        print("✅ Connected to database")
        
        # Check if tables exist
        tables = ['fm_global_tables', 'fm_global_figures', 'fm_global_vectors']
        
        for table in tables:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = $1
                )
            """, table)
            
            if exists:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' does not exist")
        
        # Create tables if they don't exist
        print("\n📝 Creating FM Global tables if they don't exist...")
        
        # Enable uuid extension
        await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Create fm_global_tables
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS fm_global_tables (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                table_number TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                section TEXT,
                page_reference TEXT,
                table_type TEXT,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create fm_global_figures
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS fm_global_figures (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                figure_number TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                section TEXT,
                page_reference TEXT,
                figure_type TEXT,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create fm_global_vectors
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS fm_global_vectors (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                content_id UUID NOT NULL,
                content_type TEXT NOT NULL CHECK (content_type IN ('table', 'figure', 'section', 'requirement')),
                content TEXT NOT NULL,
                embedding vector(1536),
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_fm_global_tables_number ON fm_global_tables(table_number);
            CREATE INDEX IF NOT EXISTS idx_fm_global_figures_number ON fm_global_figures(figure_number);
            CREATE INDEX IF NOT EXISTS idx_fm_global_vectors_content_id ON fm_global_vectors(content_id);
            CREATE INDEX IF NOT EXISTS idx_fm_global_vectors_content_type ON fm_global_vectors(content_type);
            CREATE INDEX IF NOT EXISTS idx_fm_global_vectors_embedding ON fm_global_vectors USING ivfflat (embedding vector_cosine_ops);
        """)
        
        print("✅ Tables and indexes created successfully")
        
        # Insert sample data
        print("\n📝 Inserting sample FM Global data...")
        
        # Insert sample table
        await conn.execute("""
            INSERT INTO fm_global_tables (table_number, title, content, section, page_reference, table_type)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT DO NOTHING
        """, 
            "Table 2-1",
            "Minimum Aisle Width and Spacing Requirements",
            """Minimum aisle widths based on commodity classification:
            - Class I-III Commodities: 6 ft (1.8 m) minimum aisle
            - Class IV Commodities: 8 ft (2.4 m) minimum aisle
            - Plastics Group A: 10 ft (3.0 m) minimum aisle
            - Transverse flues: 3 in. (76 mm) minimum
            - Longitudinal flues: 6 in. (152 mm) for double-row racks""",
            "Section 2: Design Criteria",
            "Page 12",
            "spacing_requirements"
        )
        
        # Insert sample figure
        await conn.execute("""
            INSERT INTO fm_global_figures (figure_number, title, description, section, page_reference, figure_type)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT DO NOTHING
        """,
            "Figure 3-2",
            "Seismic Bracing Configuration",
            "Detailed diagram showing longitudinal and transverse bracing requirements for ASRS racks in seismic zones",
            "Section 3: Structural Requirements",
            "Page 28",
            "structural_diagram"
        )
        
        print("✅ Sample data inserted")
        
        # Count records
        table_count = await conn.fetchval("SELECT COUNT(*) FROM fm_global_tables")
        figure_count = await conn.fetchval("SELECT COUNT(*) FROM fm_global_figures")
        vector_count = await conn.fetchval("SELECT COUNT(*) FROM fm_global_vectors")
        
        print(f"\n📊 Current record counts:")
        print(f"  - fm_global_tables: {table_count}")
        print(f"  - fm_global_figures: {figure_count}")
        print(f"  - fm_global_vectors: {vector_count}")
        
        await conn.close()
        print("\n✅ Database setup complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if "Tenant or user not found" in str(e):
            print("\n💡 This error suggests the database URL might be incorrect.")
            print("   Please verify your Supabase project URL and credentials.")

if __name__ == "__main__":
    asyncio.run(check_and_create_fm_tables())