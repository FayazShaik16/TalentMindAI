import sys
import os
import argparse
import asyncio

# Fix sys.path to run script from backend folder or scripts folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import async_session_factory
from app.services.analytics.monitoring import MonitoringService
from app.services.analytics.analytics import AnalyticsEngine

async def main():
    parser = argparse.ArgumentParser(description="Display dashboard statistics, system health, and AI metrics.")
    args = parser.parse_args()

    async with async_session_factory() as session:
        monitor_service = MonitoringService(session)
        analytics_engine = AnalyticsEngine(session)

        print("\n" + "=" * 80)
        print("TALENTMIND AI - RECRUITER PLATFORM SYSTEM STATUS & DIAGNOSTICS")
        print("=" * 80)

        # 1. Fetch Health Metrics
        try:
            health = await monitor_service.get_system_health()
            print("OPERATIONAL HEALTH SUMMARY:")
            print(f"  - System Status         : {health['status'].upper()}")
            print(f"  - Database Connectivity : {health['components']['database'].upper()}")
            print(f"  - Vector Storage (FAISS): {health['components']['vector_index'].upper()}")
            print(f"  - Cache Storage (SQLite): {health['components']['embedding_cache'].upper()}")
            print("-" * 80)

            # Resources Telemetry
            metrics = health["metrics"]
            print("RESOURCES TELEMETRY LOG:")
            print(f"  - CPU Usage            : {metrics['cpu_usage_percent']}%")
            print(f"  - RAM Usage            : {metrics['ram_usage_percent']}% (Available: {metrics['ram_available_mb']:.1f} MB)")
            print(f"  - Disk Storage Free    : {metrics['disk_free_gb']:.1f} GB")
            print(f"  - Cached Vectors Count : {metrics['cached_embeddings_count']}")
            print("-" * 80)

            # FAISS Details
            print("VECTOR DATABASE STATS:")
            details = metrics["faiss_details"]
            if details:
                for coll, d in details.items():
                    print(f"  Collection '{coll}':")
                    print(f"    - Elements Count     : {d.get('ntotal', 0)}")
                    print(f"    - Vector Dimensions  : {d.get('dimension', 0)}")
                    print(f"    - Index Type         : {d.get('index_type')}")
                    print(f"    - Metric             : {d.get('metric_type')}")
            else:
                print("  No active FAISS index files detected in vector_indices folder.")
            print("-" * 80)

        except Exception as e:
            print(f"Error fetching system health: {str(e)}")
            print("-" * 80)

        # 2. Fetch Performance & Hiring Analytics
        try:
            analytics = await analytics_engine.generate_hiring_analytics()
            print("AI HIRING INTEL & PERFORMANCE AVERAGES:")
            print(f"  - Candidates Evaluated  : {analytics['total_evaluated']}")
            print(f"  - Average Match Score   : {analytics['average_match_score']:.1f}%")
            print(f"  - Average Confidence    : {analytics['average_hiring_confidence']*100:.1f}%")
            
            # Recommendation Funnel
            funnel = analytics["hiring_funnel"]["counts"]
            funnel_pct = analytics["hiring_funnel"]["percentages"]
            print("  - Hiring Funnel Rates   :")
            for rec, count in funnel.items():
                print(f"      * {rec:<17}: {count} candidates ({funnel_pct.get(rec, 0.0):.1f}%)")

            # Distributions
            print("  - Experience Mix:")
            for k, v in analytics["distributions"]["experience"].items():
                print(f"      * {k:<17}: {v} profiles")
                
            print("  - Top Requested Technologies:")
            techs = analytics["top_technologies"]
            if techs:
                for item in techs[:5]:
                    print(f"      * {item['technology']:<17}: {item['count']} references")
            else:
                print("      * No tech mappings found.")

        except Exception as e:
            print(f"Error fetching hiring analytics: {str(e)}")

        print("=" * 80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
