from typing import Optional
from src.knowledge_graph.kg_client import KnowledgeGraphClient
import structlog

logger = structlog.get_logger(__name__)


class BankingKGQueries:

    def __init__(self):
        self.kg = KnowledgeGraphClient.get_instance()

    def get_customer_financial_profile(self, customer_id: str) -> dict:
        cypher = """
        MATCH (c:Customer {id: $cid})
        OPTIONAL MATCH (c)-[:HAS_ACCOUNT]->(a:Account)
        OPTIONAL MATCH (c)-[:HAS_LOAN]->(l:Loan)
        OPTIONAL MATCH (c)-[:HOLDS_PRODUCT]->(p:Product)
        RETURN
            c.id AS customer_id,
            c.name AS name,
            c.credit_score AS credit_score,
            c.kyc_status AS kyc_status,
            c.segment AS segment,
            c.annual_income AS annual_income,
            collect(DISTINCT {
                id: a.id, type: a.type,
                balance: a.balance, status: a.status,
                last_txn_date: a.last_txn_date
            }) AS accounts,
            collect(DISTINCT {
                id: l.id, type: l.type,
                emi: l.emi, outstanding: l.outstanding, status: l.status
            }) AS loans,
            collect(DISTINCT {
                id: p.id, name: p.name, category: p.category
            }) AS products
        """
        results = self.kg.run_query(cypher, {"cid": customer_id})
        return results[0] if results else {}

    def get_customer_emi_load_and_regulations(self, customer_id: str, loan_type: str) -> dict:
        cypher = """
        MATCH (c:Customer {id: $cid})
        OPTIONAL MATCH (c)-[:HAS_LOAN]->(l:Loan {status: 'active'})
        WITH c,
             collect(l) AS active_loans,
             sum(CASE WHEN l.status = 'active' THEN l.emi ELSE 0 END) AS total_emi
        OPTIONAL MATCH (p:Product)-[:GOVERNED_BY]->(r:RegulationRule)
        WHERE toLower(p.name) CONTAINS toLower($loan_type)
           OR r.applies_to CONTAINS $loan_type
        RETURN
            c.id AS customer_id,
            c.credit_score AS credit_score,
            c.annual_income AS annual_income,
            total_emi,
            size(active_loans) AS active_loan_count,
            [ln IN active_loans | {
                id: ln.id, type: ln.type,
                emi: ln.emi, outstanding: ln.outstanding
            }] AS active_loans,
            collect(DISTINCT {
                id: r.id, title: r.title,
                description: r.description, source: r.source
            }) AS applicable_regulations
        """
        results = self.kg.run_query(cypher, {"cid": customer_id, "loan_type": loan_type})
        return results[0] if results else {}

    def detect_fraud_network(self, payee_id: str) -> dict:
        cypher = """
        MATCH (t:Transaction {payee_id: $payee_id})
        OPTIONAL MATCH (t)-[:FLAGGED_BY]->(rf:RiskFlag)
        OPTIONAL MATCH (a:Account)-[:HAS_TRANSACTION]->(t)
        OPTIONAL MATCH (c:Customer)-[:HAS_ACCOUNT]->(a)
        WITH
            collect(DISTINCT t.id) AS all_txns,
            sum(t.amount) AS total_amount,
            collect(DISTINCT rf.type) AS flag_types,
            max(rf.severity) AS max_severity,
            collect(DISTINCT c.id) AS linked_customers,
            count(DISTINCT CASE WHEN t.is_flagged THEN t.id END) AS flagged_count
        RETURN
            $payee_id AS payee_id,
            size(all_txns) AS total_transactions,
            total_amount,
            flag_types,
            max_severity,
            linked_customers,
            flagged_count,
            CASE WHEN flagged_count > 2 OR max_severity = 'critical'
                 THEN true ELSE false END AS is_known_fraud_payee
        """
        results = self.kg.run_query(cypher, {"payee_id": payee_id})
        return results[0] if results else {
            "payee_id": payee_id,
            "total_transactions": 0,
            "is_known_fraud_payee": False,
        }

    def get_product_regulations(self, product_name: str) -> list:
        cypher = """
        MATCH (p:Product)
        WHERE toLower(p.name) CONTAINS toLower($name)
           OR toLower(p.category) CONTAINS toLower($name)
        OPTIONAL MATCH (p)-[:GOVERNED_BY]->(r:RegulationRule)
        RETURN
            p.id AS product_id,
            p.name AS product_name,
            p.category AS category,
            p.eligibility_criteria AS eligibility_criteria,
            p.min_balance AS min_balance,
            p.interest_rate AS interest_rate,
            collect(DISTINCT {
                id: r.id, source: r.source,
                title: r.title, description: r.description
            }) AS regulations
        """
        return self.kg.run_query(cypher, {"name": product_name})

    def get_inactive_accounts(self, customer_id: str, inactive_months: int = 6) -> dict:
        cypher = """
        MATCH (c:Customer {id: $cid})-[:HAS_ACCOUNT]->(a:Account)
        WITH c, a,
             duration.between(date(a.last_txn_date), date()).months AS months_inactive
        RETURN
            c.id AS customer_id,
            a.id AS account_id,
            a.type AS account_type,
            a.balance AS balance,
            a.status AS status,
            a.last_txn_date AS last_txn_date,
            months_inactive,
            CASE WHEN months_inactive >= $months THEN true ELSE false END AS is_inactive
        ORDER BY months_inactive DESC
        """
        results = self.kg.run_query(cypher, {"cid": customer_id, "months": inactive_months})
        return {
            "customer_id": customer_id,
            "all_accounts": results,
            "inactive_accounts": [r for r in results if r.get("is_inactive")],
            "active_accounts": [r for r in results if not r.get("is_inactive")],
        }

    def detect_fraud_ring(self) -> list:
        cypher = """
        MATCH (c1:Customer)-[:LINKED_TO]->(c2:Customer)
        MATCH (c1)-[:HAS_ACCOUNT]->(a1:Account)-[:HAS_TRANSACTION]->(t1:Transaction)
        MATCH (c2)-[:HAS_ACCOUNT]->(a2:Account)-[:HAS_TRANSACTION]->(t2:Transaction)
        WHERE t1.payee_id = t2.payee_id
          AND t1.is_flagged = true
          AND t2.is_flagged = true
        RETURN
            c1.id AS customer_1,
            c2.id AS customer_2,
            collect(DISTINCT t1.payee_id) AS common_flagged_payees,
            count(DISTINCT t1.payee_id) AS shared_payee_count
        ORDER BY shared_payee_count DESC
        LIMIT 20
        """
        return self.kg.run_query(cypher)

    def get_customer_by_id(self, customer_id: str) -> Optional[dict]:
        results = self.kg.run_query(
            "MATCH (c:Customer {id: $cid}) RETURN c",
            {"cid": customer_id},
        )
        return results[0]["c"] if results else None