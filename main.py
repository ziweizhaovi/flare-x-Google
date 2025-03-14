import asyncio
from src.flare_ai_defai.config import Config
from src.flare_ai_defai.ai_risk_analyzer import AIRiskAnalyzer
from src.flare_ai_defai.blockchain_verifier import FlareVerifier
from src.flare_ai_defai.alert_system import AlertSystem
from bigquery_fetcher import BigQueryFetcher
import pandas as pd

async def main():
    # Load configuration
    config = Config()
    
    # Initialize components
    fetcher = BigQueryFetcher()
    analyzer = AIRiskAnalyzer(config.GEMINI_API_KEY)
    verifier = FlareVerifier()
    alert_system = AlertSystem(
        gmail_user=config.GMAIL_USER,
        gmail_password=config.GMAIL_PASSWORD,
        recipient_email=config.RECIPIENT_EMAIL
    )
    
    while True:
        try:
            # Fetch and analyze pool data
            df = fetcher.fetch_liquidity_pools()
            if not df.empty:
                # Analyze transactions
                results = analyzer.analyze_dataset(df)
                
                # Get high-risk reports
                high_risk_reports = analyzer.prepare_high_risk_reports(results)
                
                if high_risk_reports:
                    # Verify on Flare blockchain
                    verification_results = await verifier.verify_transactions(high_risk_reports)
                    
                    # Send alerts for verified high-risk transactions
                    for result in verification_results:
                        if result['status'] == 'verified':
                            report = next(r for r in high_risk_reports 
                                        if r['transaction_hash'] == result['transaction_hash'])
                            
                            alert_data = {
                                'event_data': {
                                    'transaction_hash': report['transaction_hash'],
                                    'verification_tx': result['verification_tx']
                                },
                                'ai_analysis': report['risk_hash'],
                                'timestamp': str(pd.Timestamp.now())
                            }
                            
                            await alert_system.send_alert(alert_data)
            
            await asyncio.sleep(config.LIQUIDITY_POOL_QUERY_INTERVAL)
        
        except Exception as e:
            print(f"Error in main loop: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main()) 