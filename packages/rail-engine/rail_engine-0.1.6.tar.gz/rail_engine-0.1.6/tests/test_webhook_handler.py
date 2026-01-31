"""Tests for webhook handling functionality."""

import json

import pytest
from pydantic import BaseModel, ValidationError

from railtown.engine.ingest.client import RailengineIngest
from railtown.engine.ingest.models import (
    WebhookEvent,
    WebhookHandler,
    WebhookPublishingPayload,
)


class FoodDiaryItem(BaseModel):
    """Test Pydantic model."""

    food_name: str
    calories: int
    carbs: float = 0.0
    proteins: float = 0.0
    fats: float = 0.0


class SimpleModel(BaseModel):
    """Simple test model."""

    name: str
    value: int


@pytest.fixture
def sample_webhook_payload():
    """Sample webhook payload dictionary."""
    return {
        "EventId": "event-123",
        "EngineId": "engine-456",
        "ProjectId": "project-789",
        "CustomerKey": "customer-key-123",
        "Body": json.dumps(
            {
                "food_name": "Apple",
                "calories": 95,
                "carbs": 25.0,
                "proteins": 0.5,
                "fats": 0.3,
            }
        ),
    }


@pytest.fixture
def sample_webhook_payload_list(sample_webhook_payload):
    """List of sample webhook payloads."""
    payload2 = sample_webhook_payload.copy()
    payload2["EventId"] = "event-456"
    payload2["Body"] = json.dumps(
        {
            "food_name": "Banana",
            "calories": 105,
            "carbs": 27.0,
            "proteins": 1.3,
            "fats": 0.4,
        }
    )
    return [sample_webhook_payload, payload2]


class TestWebhookPublishingPayload:
    """Tests for WebhookPublishingPayload."""

    def test_webhook_publishing_payload_creation(self, sample_webhook_payload):
        """Test creating WebhookPublishingPayload from dictionary."""
        payload = WebhookPublishingPayload(**sample_webhook_payload)
        assert payload.EventId == "event-123"
        assert payload.EngineId == "engine-456"
        assert payload.ProjectId == "project-789"
        assert payload.CustomerKey == "customer-key-123"
        assert isinstance(payload.Body, str)

    def test_webhook_publishing_payload_without_customer_key(self):
        """Test WebhookPublishingPayload without CustomerKey."""
        payload_dict = {
            "EventId": "event-123",
            "EngineId": "engine-456",
            "ProjectId": "project-789",
            "Body": json.dumps({"food_name": "Apple", "calories": 95}),
        }
        payload = WebhookPublishingPayload(**payload_dict)
        assert payload.CustomerKey is None

    def test_get_body_as_valid_model(self, sample_webhook_payload):
        """Test get_body_as() with valid model."""
        payload = WebhookPublishingPayload(**sample_webhook_payload)
        item = payload.get_body_as(FoodDiaryItem)

        assert isinstance(item, FoodDiaryItem)
        assert item.food_name == "Apple"
        assert item.calories == 95
        assert item.carbs == 25.0
        assert item.proteins == 0.5
        assert item.fats == 0.3

    def test_get_body_as_invalid_model(self, sample_webhook_payload):
        """Test get_body_as() with invalid model raises ValidationError."""
        payload = WebhookPublishingPayload(**sample_webhook_payload)

        with pytest.raises(ValidationError):
            payload.get_body_as(SimpleModel)  # Missing 'name' and 'value' fields

    def test_get_body_as_invalid_json(self):
        """Test get_body_as() with invalid JSON in Body."""
        payload = WebhookPublishingPayload(
            EventId="event-123",
            EngineId="engine-456",
            ProjectId="project-789",
            Body="not valid json",
        )

        with pytest.raises(json.JSONDecodeError):
            payload.get_body_as(FoodDiaryItem)


class TestWebhookEvent:
    """Tests for WebhookEvent."""

    def test_webhook_event_creation(self, sample_webhook_payload):
        """Test creating WebhookEvent."""
        payload = WebhookPublishingPayload(**sample_webhook_payload)
        body = payload.get_body_as(FoodDiaryItem)

        event = WebhookEvent(
            EventId=payload.EventId,
            EngineId=payload.EngineId,
            ProjectId=payload.ProjectId,
            CustomerKey=payload.CustomerKey,
            body=body,
        )

        assert event.EventId == "event-123"
        assert event.EngineId == "engine-456"
        assert event.ProjectId == "project-789"
        assert event.CustomerKey == "customer-key-123"
        assert isinstance(event.body, FoodDiaryItem)
        assert event.body.food_name == "Apple"

    def test_webhook_event_without_customer_key(self):
        """Test WebhookEvent without CustomerKey."""
        body = FoodDiaryItem(food_name="Apple", calories=95)
        event = WebhookEvent(
            EventId="event-123",
            EngineId="engine-456",
            ProjectId="project-789",
            body=body,
        )
        assert event.CustomerKey is None


class TestWebhookHandler:
    """Tests for WebhookHandler."""

    def test_webhook_handler_init_with_model(self):
        """Test WebhookHandler initialization with model."""
        handler = WebhookHandler(model=FoodDiaryItem)
        assert handler.model == FoodDiaryItem

    def test_webhook_handler_init_without_model(self):
        """Test WebhookHandler initialization without model."""
        handler = WebhookHandler()
        assert handler.model is None

    def test_parse_single_dict(self, sample_webhook_payload):
        """Test parsing a single dictionary payload."""
        handler = WebhookHandler(model=FoodDiaryItem)
        events = handler.parse(sample_webhook_payload)

        assert len(events) == 1
        assert isinstance(events[0], WebhookEvent)
        assert events[0].EventId == "event-123"
        assert isinstance(events[0].body, FoodDiaryItem)
        assert events[0].body.food_name == "Apple"

    def test_parse_list_of_dicts(self, sample_webhook_payload_list):
        """Test parsing a list of dictionary payloads."""
        handler = WebhookHandler(model=FoodDiaryItem)
        events = handler.parse(sample_webhook_payload_list)

        assert len(events) == 2
        assert events[0].EventId == "event-123"
        assert events[0].body.food_name == "Apple"
        assert events[1].EventId == "event-456"
        assert events[1].body.food_name == "Banana"

    def test_parse_without_model_raises_error(self, sample_webhook_payload):
        """Test parsing without model raises ValueError."""
        handler = WebhookHandler()

        with pytest.raises(ValueError, match="Model type is required"):
            handler.parse(sample_webhook_payload)

    def test_parse_invalid_payload_structure(self):
        """Test parsing invalid payload structure."""
        handler = WebhookHandler(model=FoodDiaryItem)

        invalid_payload = {
            "EventId": "event-123",
            # Missing required fields
        }

        with pytest.raises(ValidationError):
            handler.parse(invalid_payload)

    def test_parse_invalid_body_json(self):
        """Test parsing payload with invalid body JSON."""
        handler = WebhookHandler(model=FoodDiaryItem)

        invalid_payload = {
            "EventId": "event-123",
            "EngineId": "engine-456",
            "ProjectId": "project-789",
            "Body": "not valid json",
        }

        with pytest.raises(json.JSONDecodeError):
            handler.parse(invalid_payload)

    def test_parse_body_validation_error(self):
        """Test parsing payload with body that doesn't match model."""
        handler = WebhookHandler(model=FoodDiaryItem)

        invalid_payload = {
            "EventId": "event-123",
            "EngineId": "engine-456",
            "ProjectId": "project-789",
            "Body": json.dumps({"name": "test", "value": 123}),  # Wrong structure
        }

        with pytest.raises(ValidationError):
            handler.parse(invalid_payload)


class TestRailengineIngestGetWebhookHandler:
    """Tests for RailengineIngest.get_webhook_handler()."""

    def test_get_webhook_handler_with_model(self, sample_engine_token):
        """Test get_webhook_handler() when client has model."""
        client = RailengineIngest(engine_token=sample_engine_token, model=FoodDiaryItem)
        handler = client.get_webhook_handler()

        assert isinstance(handler, WebhookHandler)
        assert handler.model == FoodDiaryItem

    def test_get_webhook_handler_without_model_raises_error(self, sample_engine_token):
        """Test get_webhook_handler() without model raises ValueError."""
        client = RailengineIngest(engine_token=sample_engine_token)

        with pytest.raises(ValueError, match="Model type is required"):
            client.get_webhook_handler()

    def test_get_webhook_handler_usage(self, sample_engine_token, sample_webhook_payload):
        """Test using handler from client to parse webhook."""
        client = RailengineIngest(engine_token=sample_engine_token, model=FoodDiaryItem)
        handler = client.get_webhook_handler()

        events = handler.parse(sample_webhook_payload)

        assert len(events) == 1
        assert events[0].body.food_name == "Apple"
        assert events[0].EventId == "event-123"
