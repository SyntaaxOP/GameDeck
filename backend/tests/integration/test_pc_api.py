def test_pc_profile_and_snapshot(api_client):
    assert api_client.get('/api/v1/pc/profile').json() is None
    saved=api_client.put('/api/v1/pc/profile',json={'name':'Main rig','cpu':'Ryzen','gpu':'Radeon','memory_gb':32,'storage':'2 TB NVMe'})
    assert saved.status_code==200 and saved.json()['memory_gb']==32
    assert api_client.get('/api/v1/pc/profile').json()['name']=='Main rig'
    snapshot=api_client.get('/api/v1/pc/snapshot')
    assert snapshot.status_code==200
    assert snapshot.json()['memory_gb']>0 and snapshot.json()['storage_gb']>0

def test_pc_profile_validates_memory(api_client):
    assert api_client.put('/api/v1/pc/profile',json={'name':'Invalid','memory_gb':0}).status_code==422
