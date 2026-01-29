"""Tests for terminal tool."""


def test_execute_echo(client):
    """Test executing simple echo command."""
    response = client.post(
        "/terminal/execute",
        json={"command": "echo hello", "timeout_seconds": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert "hello" in data["output"]
    assert data["exit_code"] == 0


def test_execute_truncation_summary(client):
    """Test that large output is truncated and summarized."""
    response = client.post(
        "/terminal/execute",
        json={
            "command": "for i in $(seq 1 30); do echo \"line $i\"; done",
            "timeout_seconds": 30,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["exit_code"] == 0
    assert data["truncated"] is True
    assert "lines truncated" in data["output"]
    assert data["summary"]
