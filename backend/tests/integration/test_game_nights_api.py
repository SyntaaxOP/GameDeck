from datetime import UTC, datetime

def test_game_night_crud_and_discord_announcement(api_client):
    created=api_client.post('/api/v1/game-nights',json={'title':'Friday squad','scheduled_at':datetime(2026,8,14,13,tzinfo=UTC).isoformat(),'duration_minutes':180,'attendees':[{'name':'Alex','response':'confirmed'},{'name':'Sam','response':'maybe'}]})
    assert created.status_code==201,created.text
    night_id=created.json()['id']
    assert api_client.get('/api/v1/game-nights').json()['total']==1
    message=api_client.get(f'/api/v1/game-nights/{night_id}/discord-announcement').json()['message']
    assert 'Friday squad' in message and 'Alex' in message and 'Sam' in message
    assert api_client.patch(f'/api/v1/game-nights/{night_id}',json={'status':'completed'}).json()['status']=='completed'
    assert api_client.delete(f'/api/v1/game-nights/{night_id}').status_code==204

def test_game_night_rejects_duplicate_attendee_names(api_client):
    response=api_client.post('/api/v1/game-nights',json={'title':'Duplicates','scheduled_at':datetime(2026,8,14,13,tzinfo=UTC).isoformat(),'attendees':[{'name':'Alex','response':'confirmed'},{'name':'alex','response':'maybe'}]})
    assert response.status_code==422
