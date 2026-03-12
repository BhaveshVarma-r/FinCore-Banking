import json
import random
from pathlib import Path
from src.knowledge_graph.kg_client import KnowledgeGraphClient
import structlog

logger = structlog.get_logger(__name__)
DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _load(filename: str) -> list:
    with open(DATA_DIR / filename) as f:
        return json.load(f)


def seed_all():
    kg = KnowledgeGraphClient.get_instance()
    if not kg.health_check():
        raise ConnectionError("Cannot connect to Neo4j AuraDB")

    customers = _load("mock_customers.json")
    accounts = _load("mock_accounts.json")
    transactions = _load("mock_transactions.json")
    loans = _load("mock_loans.json")
    products = _load("mock_products.json")
    regulations = _load("mock_regulation_rules.json")

    logger.info("kg.seeding_started")
    kg.run_write_query("MATCH (n) DETACH DELETE n")

    # Constraints
    for constraint in [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Account) REQUIRE a.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Loan) REQUIRE l.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Transaction) REQUIRE t.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (r:RegulationRule) REQUIRE r.id IS UNIQUE",
    ]:
        try:
            kg.run_write_query(constraint)
        except Exception:
            pass

    # Customers
    for c in customers:
        kg.run_write_query("""
            MERGE (c:Customer {id: $id})
            SET c.name=$name, c.pan=$pan, c.email=$email, c.phone=$phone,
                c.credit_score=$credit_score, c.kyc_status=$kyc_status,
                c.segment=$segment, c.annual_income=$annual_income,
                c.device_id=$device_id, c.created_at=$created_at
        """, c)

    # Accounts
    for a in accounts:
        kg.run_write_query("""
            MERGE (a:Account {id: $id})
            SET a.type=$type, a.balance=$balance, a.status=$status,
                a.last_txn_date=$last_txn_date, a.branch=$branch,
                a.ifsc=$ifsc, a.opened_date=$opened_date, a.min_balance=$min_balance
        """, a)
        kg.run_write_query("""
            MATCH (c:Customer {id: $cid}), (a:Account {id: $id})
            MERGE (c)-[:HAS_ACCOUNT]->(a)
        """, {"cid": a["customer_id"], "id": a["id"]})

    # Transactions
    flag_counter = 1
    for t in transactions:
        kg.run_write_query("""
            MERGE (t:Transaction {id: $id})
            SET t.amount=$amount, t.timestamp=$timestamp, t.payee_id=$payee_id,
                t.payee_name=$payee_name, t.channel=$channel, t.risk_score=$risk_score,
                t.type=$type, t.description=$description, t.is_flagged=$is_flagged
        """, t)
        kg.run_write_query("""
            MATCH (a:Account {id: $aid}), (t:Transaction {id: $id})
            MERGE (a)-[:HAS_TRANSACTION]->(t)
        """, {"aid": t["account_id"], "id": t["id"]})
        if t["is_flagged"]:
            flag_id = f"FLAG{flag_counter:04d}"
            flag_counter += 1
            severity = "critical" if t["risk_score"] > 0.9 else "high"
            kg.run_write_query("""
                MERGE (rf:RiskFlag {id: $fid})
                SET rf.type=$type, rf.severity=$severity, rf.flagged_date=$date
            """, {
                "fid": flag_id,
                "type": random.choice(["unusual_amount", "unknown_payee", "geo_anomaly"]),
                "severity": severity,
                "date": t["timestamp"][:10],
            })
            kg.run_write_query("""
                MATCH (t:Transaction {id: $tid}), (rf:RiskFlag {id: $fid})
                MERGE (t)-[:FLAGGED_BY]->(rf)
            """, {"tid": t["id"], "fid": flag_id})

    # Loans
    for l in loans:
        kg.run_write_query("""
            MERGE (l:Loan {id: $id})
            SET l.type=$type, l.amount=$amount, l.outstanding=$outstanding,
                l.emi=$emi, l.interest_rate=$interest_rate,
                l.tenure_months=$tenure_months, l.status=$status,
                l.disbursed_date=$disbursed_date, l.next_emi_date=$next_emi_date
        """, l)
        kg.run_write_query("""
            MATCH (c:Customer {id: $cid}), (l:Loan {id: $id})
            MERGE (c)-[:HAS_LOAN]->(l)
        """, {"cid": l["customer_id"], "id": l["id"]})

    # Products
    for p in products:
        kg.run_write_query("""
            MERGE (p:Product {id: $id})
            SET p.name=$name, p.category=$category, p.min_balance=$min_balance,
                p.eligibility_criteria=$eligibility_criteria, p.interest_rate=$interest_rate
        """, p)

    # Regulations
    for r in regulations:
        kg.run_write_query("""
            MERGE (r:RegulationRule {id: $id})
            SET r.source=$source, r.title=$title, r.description=$description,
                r.effective_date=$effective_date, r.applies_to=$applies_to
        """, r)

    # Product → Regulation links
    mapping = {
        "home_loan": ["PROD004"], "personal_loan": ["PROD005"],
        "msme_loan": ["PROD007"], "credit_card": ["PROD012", "PROD013"],
        "all_accounts": ["PROD001", "PROD002", "PROD003", "PROD014", "PROD015"],
        "dormant_accounts": ["PROD001", "PROD002", "PROD003"],
        "all_data": ["PROD001","PROD002","PROD003","PROD004","PROD005",
                     "PROD006","PROD007","PROD008","PROD009","PROD010",
                     "PROD011","PROD012","PROD013","PROD014","PROD015"],
    }
    for reg in regulations:
        for prod_id in mapping.get(reg["applies_to"], []):
            kg.run_write_query("""
                MATCH (p:Product {id: $pid}), (r:RegulationRule {id: $rid})
                MERGE (p)-[:GOVERNED_BY]->(r)
            """, {"pid": prod_id, "rid": reg["id"]})

    # Customer → Product links
    type_to_prod = {
        "savings": "PROD001", "premium_savings": "PROD002",
        "current": "PROD003", "fd": "PROD009", "rd": "PROD010",
    }
    for a in accounts:
        prod_id = type_to_prod.get(a["type"])
        if prod_id:
            kg.run_write_query("""
                MATCH (c:Customer {id: $cid}), (p:Product {id: $pid})
                MERGE (c)-[:HOLDS_PRODUCT]->(p)
            """, {"cid": a["customer_id"], "pid": prod_id})

    # Loan → Product links
    loan_to_prod = {
        "home": "PROD004", "personal": "PROD005", "car": "PROD006",
        "msme": "PROD007", "education": "PROD008", "gold": "PROD011",
    }
    for l in loans:
        prod_id = loan_to_prod.get(l["type"])
        if prod_id:
            kg.run_write_query("""
                MATCH (l:Loan {id: $lid}), (p:Product {id: $pid})
                MERGE (l)-[:IS_OF_PRODUCT]->(p)
            """, {"lid": l["id"], "pid": prod_id})

    # Fraud network: LINKED_TO by shared device
    device_map: dict[str, list] = {}
    for c in customers:
        device_map.setdefault(c["device_id"], []).append(c["id"])
    for device_id, cust_ids in device_map.items():
        if len(cust_ids) > 1:
            for i in range(len(cust_ids)):
                for j in range(i + 1, len(cust_ids)):
                    kg.run_write_query("""
                        MATCH (c1:Customer {id: $id1}), (c2:Customer {id: $id2})
                        MERGE (c1)-[:LINKED_TO {reason: 'shared_device', device_id: $did}]->(c2)
                    """, {"id1": cust_ids[i], "id2": cust_ids[j], "did": device_id})

    logger.info("kg.seeding_complete")
    print("Knowledge Graph seeded successfully!")


if __name__ == "__main__":
    seed_all()