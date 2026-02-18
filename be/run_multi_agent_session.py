import json
import os
from agents import AgentOrchestrator, FinancialRatioAgent, DataValidationAgent, QualityCheckAgent, FactCheckingAgent

SESSIONS_DIR = os.path.join(os.path.dirname(__file__), 'uploads', 'sessions')

def load_session(sid):
    path = os.path.join(SESSIONS_DIR, f"{sid}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_for_session(sid):
    session = load_session(sid)
    bs_data = session.get('balance_sheet_data')
    pl_data = session.get('profit_and_loss') or {}

    orchestrator = AgentOrchestrator(max_workers=4)

    # Create agents and remove extraction dependencies so they run directly on provided data
    fr = FinancialRatioAgent()
    fr.dependencies = []
    dv = DataValidationAgent()
    dv.dependencies = []
    qc = QualityCheckAgent()
    qc.dependencies = []
    fc = FactCheckingAgent()
    fc.dependencies = []

    orchestrator.register_agents([fr, dv, qc, fc])

    input_data = {
        'balance_sheet_data': bs_data,
        'pl_data': pl_data
    }
    context = { 'session_id': sid }

    print(f"Running agents for session: {sid}")
    results = orchestrator.execute_agents(input_data, context)

    summary = orchestrator.get_summary()
    print('\n--- Execution Summary ---')
    print(json.dumps(summary, indent=2))

    print('\n--- Agent Outputs ---')
    for name, res in results.items():
        print(f"\nAgent: {name}")
        try:
            print(json.dumps({'status': res.status.value, 'error': res.error, 'execution_time': res.execution_time, 'output': res.output}, default=str, indent=2)[:2000])
        except Exception as e:
            print(f"(Could not serialize output: {e})")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: python run_multi_agent_session.py <session_id>')
        sys.exit(1)
    sid = sys.argv[1]
    run_for_session(sid)
