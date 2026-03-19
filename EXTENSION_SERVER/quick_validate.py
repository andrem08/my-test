import json
files = ["n8n_diagrams/VHSYS-health-v1.json","n8n_diagrams/VHSYS-update_services-v1.json","n8n_diagrams/VHSYS-get_update_extension_service_data-v1.json","n8n_diagrams/VHSYS-cc_status-v1.json","n8n_diagrams/VHSYS-cc_next_url-v1.json","n8n_diagrams/VHSYS-cc_report-v1.json"]
for f in files:
    d=json.load(open(f))
    n=[x for x in d['nodes'] if x['id'].endswith('-001')][0]
    ok = n['type']=='n8n-nodes-base.executeWorkflowTrigger' and n['name']=='When called by another workflow'
    print(f"{'✅' if ok else '❌'} {f.split('/')[-1]}")
