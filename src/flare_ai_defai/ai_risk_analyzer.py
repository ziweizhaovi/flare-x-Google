import google.generativeai as genai
import pandas as pd
from typing import Tuple, Dict
import json

class AIRiskAnalyzer:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Use the correct model name
        self.model = genai.GenerativeModel('gemini-2.0-flash')  # or try 'gemini-1.0-pro-latest'

    def analyze_rug_pull(self, row: pd.Series) -> Tuple[str, str]:
        """
        Analyze a transaction for potential rug pull risks
        """
        try:
            prompt = f"""
            Analyze the following Uniswap transaction and classify its risk level as Low, Medium, or High:

            - Transaction Hash: {row['transaction_hash']}
            - Trader: {row['trader']}
            - ETH Transferred: {row['eth_transferred']}
            - Token Transferred: {row['token_value_transferred']}
            - Gas Fee (ETH): {row['gas_fee_eth']}
            - Gas Price (Gwei): {row['gas_price_gwei']}

            Consider the following:
            - Is there a large liquidity withdrawal?
            - Did the pool's liquidity drop sharply?
            - Are tokens being sold in large amounts?
            - Is this behavior similar to past rug pulls?
            - Is there any unusual pattern in gas fees?

            Your response should be in this structured format:
            ```
            Risk Score: [Low/Medium/High]
            Analysis: [Short explanation of why this transaction is assigned this risk score]
            ```
            """

            response = self.model.generate_content(prompt)
            ai_response = response.text.split("\n")

            risk_score = "Unknown"
            analysis = "No AI Response"

            for line in ai_response:
                if "Risk Score:" in line:
                    risk_score = line.split("Risk Score:")[1].strip()
                if "Analysis:" in line:
                    analysis = line.split("Analysis:")[1].strip()

            return risk_score, analysis
        except Exception as e:
            print(f"Error analyzing transaction: {e}")
            return "Error", str(e)

    def analyze_dataset(self, csv_path: str, output_path: str):
        """
        Analyze an entire dataset of transactions
        """
        try:
            # Load the dataset
            df = pd.read_csv(csv_path)
            
            # Apply AI analysis to each row
            df[["risk_score", "ai_analysis"]] = df.apply(
                lambda row: pd.Series(self.analyze_rug_pull(row)), 
                axis=1
            )
            
            # Save the results
            df.to_csv(output_path, index=False)
            return df
        except Exception as e:
            print(f"Error processing dataset: {e}")
            return None

    def generate_risk_hash(self, risk_score: str, analysis: str) -> str:
        """
        Generate a hash of the risk analysis for blockchain storage
        """
        risk_data = {
            "risk_score": risk_score,
            "analysis": analysis,
            "timestamp": str(pd.Timestamp.now())
        }
        return json.dumps(risk_data)

    def prepare_high_risk_reports(self, results_df: pd.DataFrame) -> list:
        """
        Prepare high-risk transactions for blockchain verification
        """
        high_risk_reports = []
        
        # Filter for high-risk transactions
        high_risk_df = results_df[results_df['risk_score'] == 'High']
        
        for _, row in high_risk_df.iterrows():
            report = {
                'transaction_hash': row['transaction_hash'],
                'risk_hash': self.generate_risk_hash(
                    row['risk_score'],
                    row['ai_analysis']
                )
            }
            high_risk_reports.append(report)
        
        return high_risk_reports

# Example usage
if __name__ == "__main__":
    # Initialize the analyzer with your API key
    analyzer = AIRiskAnalyzer(api_key="AIzaSyBvsGgBURt0NXLgLgDa0IOJ0i4bx9ZEJ9Y")
    
    # Analyze the dataset
    results = analyzer.analyze_dataset(
        csv_path='/Users/zhao/Downloads/example_data.csv',
        output_path='/Users/zhao/Downloads/example_data_with_ai_risk.csv'
    )
    
    # Print some results
    print("\nAnalysis Results:")
    print(f"Total transactions analyzed: {len(results)}")
    print("\nRisk Distribution:")
    print(results['risk_score'].value_counts())
    
    # Print a sample high-risk transaction
    high_risk = results[results['risk_score'] == 'High'].iloc[0] if 'High' in results['risk_score'].values else None
    if high_risk is not None:
        print("\nSample High Risk Transaction:")
        print(f"Transaction Hash: {high_risk['transaction_hash']}")
        print(f"Risk Score: {high_risk['risk_score']}")
        print(f"Analysis: {high_risk['ai_analysis']}") 