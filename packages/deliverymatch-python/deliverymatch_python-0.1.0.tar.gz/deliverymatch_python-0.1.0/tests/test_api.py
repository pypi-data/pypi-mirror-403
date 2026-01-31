import datetime
import json as json_module
from http import HTTPStatus
from unittest.mock import MagicMock, patch

import httpx
import pytest

from deliverymatch import Client as ApiClient
from deliverymatch.api.default import (
    add_document,
    close_linehaul,
    delete_document,
    download_attachment,
    get_design,
    get_document,
    get_label,
    get_linehauls,
    get_locations,
    get_services,
    get_shipment,
    get_shipments,
    get_status,
    insert_shipment,
    insert_shipments,
    push_status_events,
    retrieve_all_document_ids,
    test_api_connection,
    update_document,
    update_routes,
    update_shipment,
    update_shipment_method,
)
from deliverymatch.models import (
    AddDocumentBody,
    AddDocumentResponse201,
    AddDocumentResponse201DocumentType,
    AddDocumentResponse201FileType,
    Address,
    CloseLinehaulBody,
    CloseLinehaulBodyAddress,
    CloseLinehaulResponse200,
    Client,
    ClientAction,
    ClientMethod,
    Contact,
    Customer,
    Document,
    DocumentDocumentType,
    DocumentFileType,
    DownloadAttachmentBody,
    GetDesignBody,
    GetDesignResponse200,
    GetDocumentResponse200,
    GetLabelBody,
    GetLabelResponse200,
    GetLinehaulsResponse200,
    GetLocationsBody,
    GetLocationsBodyAddress,
    GetLocationsResponse200,
    GetServicesBody,
    GetServicesResponse200,
    GetShipmentBody,
    GetShipmentResponse200,
    GetShipmentsBody,
    GetShipmentsBodyStatus,
    GetShipmentsResponse200,
    GetStatusBody,
    GetStatusBodyShipment,
    GetStatusResponse200,
    GetStatusResponse200Shipment,
    InsertShipmentBody,
    InsertShipmentBodyQuote,
    InsertShipmentResponse200,
    InsertShipmentsBody,
    InsertShipmentsBodyQuote,
    InsertShipmentsResponse200,
    Method,
    Product,
    PushStatusEventsBody,
    PushStatusEventsBodyEventsItem,
    PushStatusEventsBodyShipment,
    PushStatusEventsResponse200,
    Reference,
    Sender,
    Shipment,
    Status,
    UpdateDocumentBody,
    UpdateRoutesBody,
    UpdateRoutesBodyAdjustment,
    UpdateRoutesBodyFilter,
    UpdateRoutesResponse200,
    UpdateShipmentBody,
    UpdateShipmentBodyShipment,
    UpdateShipmentMethodBody,
    UpdateShipmentMethodBodyAction,
    UpdateShipmentMethodResponse200,
    UpdateShipmentResponse200,
)
from deliverymatch.types import File


@pytest.fixture
def api_client():
    return ApiClient(base_url="https://engine.deliverymatch.eu/api/v1")


@pytest.fixture
def mock_response():
    def _mock(status_code=200, json_data=None):
        data = json_data or {}
        response = MagicMock(spec=httpx.Response)
        response.status_code = status_code
        response.content = json_module.dumps(data).encode()
        response.headers = {"content-type": "application/json"}
        response.json.return_value = data
        return response
    return _mock


def test_insert_shipment(api_client, mock_response):
    body = InsertShipmentBody(
        client=Client(
            id=123,
            channel="webshop",
            callback="https://example.com/callback",
            action=ClientAction.SELECT,
            method=ClientMethod.FIRST,
            filter_=True,
            transportlabel=True,
            copy=False,
        ),
        shipment=Shipment(
            order_number="ORD-12345",
            reference="REF-12345",
            language="nl",
            currency="EUR",
            first_pickup_date="2024-01-20",
            delivery_date="2024-01-22",
            note="Leave at door",
            instructions="Ring bell twice",
        ),
        customer=Customer(
            id=456,
            address=Address(
                name="Jan Jansen",
                company_name="Acme BV",
                address1="Hoofdstraat 1A",
                address2="2nd floor",
                street="Hoofdstraat",
                house_nr=1,
                house_nr_ext="A",
                postcode="1234AB",
                city="Amsterdam",
                state="NH",
                country="NL",
                zone="zone-1",
            ),
            billing=Address(
                name="Billing Dept",
                company_name="Acme BV",
                address1="Factuurstraat 10",
                street="Factuurstraat",
                house_nr=10,
                postcode="1234CD",
                city="Amsterdam",
                country="NL",
            ),
            contact=Contact(
                phone_number="+31612345678",
                email="jan@acme.nl",
            ),
        ),
        quote=InsertShipmentBodyQuote(
            product=[
                Product(
                    id="SKU-001",
                    package_num=1.0,
                    warehouse="1",
                    transportlabel=False,
                    location="A1-B2",
                    description="T-Shirt Blue XL",
                    content="Cotton T-Shirt",
                    sku="TSHIRT-BLU-XL",
                    ean="1234567890123",
                    hs_code="6109100010",
                    quantity=2,
                    value=25.00,
                    weight=0.3,
                    length=30.0,
                    width=20.0,
                    height=5.0,
                    volume=0.003,
                    stock=True,
                    country_of_origin="NL",
                    item_group="clothing",
                    amount_per_package=1.0,
                ),
            ]
        ),
        sender=Sender(
            id="sender-001",
            address=Address(
                name="Warehouse Manager",
                company_name="Acme Warehouse",
                address1="Industrieweg 10",
                street="Industrieweg",
                house_nr=10,
                postcode="5678CD",
                city="Rotterdam",
                country="NL",
            ),
            contact=Contact(
                phone_number="+31687654321",
                email="warehouse@acme.nl",
            ),
        ),
        price_incl=50.00,
        price_excl=41.32,
        price_currency="EUR",
        weight=0.6,
        fragile_goods=False,
        dangerous_goods=False,
    )

    response_data = {
        "status": "success",
        "code": 1101,
        "message": "Shipment created",
        "shipmentID": 1000001,
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(200, response_data)):
        response = insert_shipment.sync_detailed(
            client=api_client, client_header=123, apikey="test-key", body=body,
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, InsertShipmentResponse200)
    assert response.parsed.status == "success"
    assert response.parsed.code == 1101
    assert response.parsed.message == "Shipment created"
    assert response.parsed.shipment_id == 1000001


def test_insert_shipments(api_client, mock_response):
    body = InsertShipmentsBody(
        client=Client(
            id=123,
            channel="bulk-import",
            action=ClientAction.SAVE,
        ),
        shipment=Shipment(
            order_number="BULK-001",
            reference="BULK-REF",
            language="nl",
            currency="EUR",
        ),
        customer=Customer(
            address=Address(
                name="Bulk Customer",
                company_name="Bulk Corp",
                address1="Bulkstraat 99",
                street="Bulkstraat",
                house_nr=99,
                postcode="9999ZZ",
                city="Bulkstad",
                country="NL",
            ),
            contact=Contact(
                phone_number="+31699999999",
                email="bulk@example.com",
            ),
        ),
        quote=InsertShipmentsBodyQuote(
            product=[
                Product(
                    id="BULK-ITEM-001",
                    description="Bulk Item",
                    content="Mixed goods",
                    sku="BULK-SKU",
                    quantity=10,
                    value=5.00,
                    weight=0.25,
                    length=10.0,
                    width=10.0,
                    height=10.0,
                )
            ]
        ),
        price_incl=50.00,
        price_excl=41.32,
        price_currency="EUR",
        weight=2.5,
        fragile_goods=True,
        dangerous_goods=False,
    )

    response_data = {
        "status": "success",
        "code": 1101,
        "message": "Shipments created",
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(200, response_data)):
        response = insert_shipments.sync_detailed(
            client=api_client, client_header=123, apikey="test-key", body=body,
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, InsertShipmentsResponse200)
    assert response.parsed.status == "success"
    assert response.parsed.code == 1101
    assert response.parsed.message == "Shipments created"


def test_get_shipment(api_client, mock_response):
    body = GetShipmentBody(
        shipment=Reference(
            id=1000001,
            order_number="ORD-12345",
        ),
    )

    response_data = {
        "fragileGoods": False,
        "dangerousGoods": True,
        "priceIncl": 50.00,
        "weight": 0.6,
        "colli": 1,
        "barcodes": ["DM123456789"],
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(200, response_data)):
        response = get_shipment.sync_detailed(
            client=api_client, client_header=123, apikey="test-key", body=body,
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, GetShipmentResponse200)
    assert response.parsed.fragile_goods is False
    assert response.parsed.dangerous_goods is True
    assert response.parsed.price_incl == 50.00
    assert response.parsed.weight == 0.6
    assert response.parsed.colli == 1
    assert response.parsed.barcodes == ["DM123456789"]


def test_get_shipments(api_client, mock_response):
    body = GetShipmentsBody(
        date_from="2024-01-01",
        date_to="2024-01-31",
        status=GetShipmentsBodyStatus.BOOKED,
        channel="webshop",
    )

    response_data = {
        "shipments": [
            {"id": 1000001, "orderNumber": "ORD-001"},
            {"id": 1000002, "orderNumber": "ORD-002"},
        ],
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(200, response_data)):
        response = get_shipments.sync_detailed(
            client=api_client, client_header=123, apikey="test-key", body=body,
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, GetShipmentsResponse200)
    assert isinstance(response.parsed.shipments, list)
    assert len(response.parsed.shipments) == 2
    assert response.parsed.shipments[0].id == 1000001
    assert response.parsed.shipments[1].id == 1000002


def test_update_shipment(api_client, mock_response):
    body = UpdateShipmentBody(
        client=Client(id=123),
        shipment=UpdateShipmentBodyShipment(
            id=1000001,
            status=Status.BOOKED,
            order_number="ORD-12345-UPDATED",
            reference="REF-UPDATED",
            note="Updated delivery instructions",
            delivery_date="2024-01-25",
        ),
        customer=Customer(
            address=Address(
                name="Updated Name",
                company_name="Updated Corp",
                address1="Newstreet 1",
                street="Newstreet",
                house_nr=1,
                postcode="1111AA",
                city="Newcity",
                country="NL",
            ),
            contact=Contact(
                phone_number="+31611111111",
                email="updated@example.com",
            ),
        ),
        price_incl=75.00,
        price_excl=61.98,
        price_currency="EUR",
        weight=1.2,
        fragile_goods=True,
        dangerous_goods=False,
    )

    response_data = {
        "status": "success",
        "code": 1103,
        "message": "Shipment updated",
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(200, response_data)):
        response = update_shipment.sync_detailed(
            client=api_client, client_header=123, apikey="test-key", body=body,
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, UpdateShipmentResponse200)
    assert response.parsed.status == "success"
    assert response.parsed.code == 1103
    assert response.parsed.message == "Shipment updated"


def test_update_shipment_method(api_client, mock_response):
    body = UpdateShipmentMethodBody(
        shipment=Reference(
            id=1000001,
            order_number="ORD-12345",
        ),
        shipment_method=Method(id="method-uuid-from-insert-response"),
        action=UpdateShipmentMethodBodyAction.BOOK,
    )

    response_data = {
        "status": "success",
        "code": 1104,
        "message": "Method updated",
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(200, response_data)):
        response = update_shipment_method.sync_detailed(
            client=api_client, client_header=123, apikey="test-key", body=body,
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, UpdateShipmentMethodResponse200)
    assert response.parsed.status == "success"
    assert response.parsed.code == 1104
    assert response.parsed.message == "Method updated"


def test_get_status(api_client, mock_response):
    body = GetStatusBody(
        shipment=GetStatusBodyShipment(
            id=1000001,
            order_number="ORD-12345",
        ),
        channel="webshop",
        date_from="2024-01-01",
        date_to="2024-01-31",
        is_incremental=False,
    )

    response_data = {
        "shipment": {"shipmentID": 1000001, "orderNumber": "ORD-12345"},
        "events": [
            {
                "shipmentId": 1000001,
                "trackingNumber": "DM123456789",
                "mainStatus": "delivered",
                "eventDate": "2024-01-15T14:30:00",
                "code": "DELIVERED",
                "description": "Package delivered",
                "city": "Amsterdam",
                "postalCode": "1234AB",
                "country": "NL",
                "latitude": "52.3676",
                "longitude": "4.9041",
                "acceptedBy": "J. Jansen",
            },
        ],
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(200, response_data)):
        response = get_status.sync_detailed(
            client=api_client, client_header=123, apikey="test-key", body=body,
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, GetStatusResponse200)
    shipment = response.parsed.shipment
    assert isinstance(shipment, GetStatusResponse200Shipment)
    assert shipment.shipment_id == 1000001
    assert shipment.order_number == "ORD-12345"
    events = response.parsed.events
    assert isinstance(events, list)
    assert len(events) == 1
    assert events[0].code == "DELIVERED"
    assert events[0].description == "Package delivered"


def test_push_status_events(api_client, mock_response):
    body = PushStatusEventsBody(
        shipment=PushStatusEventsBodyShipment(
            id=1000001,
            order_number="ORD-12345",
        ),
        events=[
            PushStatusEventsBodyEventsItem(
                tracking_number="DM123456789",
                status_code="DELIVERED",
                description="Package successfully delivered",
                date=datetime.datetime(2024, 1, 15, 14, 30, 0),
                city="Amsterdam",
                postal_code="1234AB",
                country="NL",
                latitude="52.3676",
                longitude="4.9041",
                accepted_by="J. Jansen",
                remark="Left at neighbor",
            ),
        ],
    )

    response_data = {
        "status": "success",
        "code": 1302,
        "message": "Events pushed",
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(200, response_data)):
        response = push_status_events.sync_detailed(
            client=api_client, client_header=123, apikey="test-key", body=body,
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, PushStatusEventsResponse200)
    assert response.parsed.status == "success"
    assert response.parsed.code == 1302
    assert response.parsed.message == "Events pushed"


def test_get_label(api_client, mock_response):
    body = GetLabelBody(
        shipment=Reference(
            id=1000001,
            order_number="ORD-12345",
        ),
        sequence=1,
        end_of_shipment=False,
    )

    response_data = {
        "status": "success",
        "code": 1401,
        "message": "Label retrieved",
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(200, response_data)):
        response = get_label.sync_detailed(
            client=api_client, client_header=123, apikey="test-key", body=body,
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, GetLabelResponse200)
    assert response.parsed.status == "success"
    assert response.parsed.code == 1401
    assert response.parsed.message == "Label retrieved"


def test_get_locations(api_client, mock_response):
    body = GetLocationsBody(
        shipment=Reference(
            id=1000001,
            order_number="ORD-12345",
        ),
        address=GetLocationsBodyAddress(
            address1="Hoofdstraat 1",
            postcode="1234AB",
            city="Amsterdam",
            country="NL",
        ),
    )

    response_data = {
        "status": "success",
        "code": 1501,
        "message": "Locations found",
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(200, response_data)):
        response = get_locations.sync_detailed(
            client=api_client, client_header=123, apikey="test-key", body=body,
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, GetLocationsResponse200)
    assert response.parsed.status == "success"
    assert response.parsed.code == 1501
    assert response.parsed.message == "Locations found"


def test_get_services(api_client, mock_response):
    body = GetServicesBody(
        country_from="NL",
        country_to="DE",
    )

    response_data = {
        "services": {},
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(200, response_data)):
        response = get_services.sync_detailed(
            client=api_client, client_header=123, apikey="test-key", body=body,
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, GetServicesResponse200)
    assert response.parsed.services is not None


def test_get_design(api_client, mock_response):
    body = GetDesignBody(
        language="nl",
        logo=True,
    )

    response_data = {
        "status": "success",
        "code": 1701,
        "message": "Design retrieved",
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(200, response_data)):
        response = get_design.sync_detailed(
            client=api_client, client_header=123, apikey="test-key", body=body,
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, GetDesignResponse200)
    assert response.parsed.status == "success"
    assert response.parsed.code == 1701
    assert response.parsed.message == "Design retrieved"


def test_add_document(api_client, mock_response):
    body = AddDocumentBody(
        data="base64-encoded-pdf-content",
        document_type="CMR",
        file_type="pdf",
    )

    response_data = {
        "id": 12345,
        "documentType": "CMR",
        "fileType": "PDF",
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(201, response_data)):
        response = add_document.sync_detailed(
            shipment_id="1000001",
            client=api_client,
            body=body,
        )

    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.parsed, AddDocumentResponse201)
    assert response.parsed.id == 12345
    assert response.parsed.document_type == AddDocumentResponse201DocumentType.CMR
    assert response.parsed.file_type == AddDocumentResponse201FileType.PDF


def test_get_document(api_client, mock_response):
    response_data = {
        "id": 12345,
        "data": "base64-encoded-content",
        "documentType": "CMR",
        "fileType": "pdf",
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(200, response_data)):
        response = get_document.sync_detailed(
            shipment_id="1000001",
            id="doc-123",
            client=api_client,
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, GetDocumentResponse200)
    assert response.parsed.id == 12345
    assert response.parsed.data == "base64-encoded-content"
    assert response.parsed.document_type == "CMR"
    assert response.parsed.file_type == "pdf"


def test_update_document(api_client, mock_response):
    body = UpdateDocumentBody(
        data="new-base64-encoded-content",
        document_type="CMR",
        file_type="pdf",
    )

    response_data = {
        "data": "new-base64-encoded-content",
        "documentType": "CMR",
        "fileType": "pdf",
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(201, response_data)):
        response = update_document.sync_detailed(
            shipment_id="1000001",
            id="doc-123",
            client=api_client,
            body=body,
        )

    assert response.status_code == HTTPStatus.CREATED
    assert isinstance(response.parsed, Document)
    assert response.parsed.data == "new-base64-encoded-content"
    assert response.parsed.document_type == DocumentDocumentType.CMR
    assert response.parsed.file_type == DocumentFileType.PDF


def test_delete_document(api_client, mock_response):
    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(204)):
        response = delete_document.sync_detailed(
            shipment_id="1000001",
            id="doc-123",
            client=api_client,
        )

    assert response.status_code == HTTPStatus.NO_CONTENT


def test_retrieve_all_document_ids(api_client, mock_response):
    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(200)):
        response = retrieve_all_document_ids.sync_detailed(
            shipment_id="1000001",
            client=api_client,
        )

    assert response.status_code == HTTPStatus.OK


def test_download_attachment(api_client):
    body = DownloadAttachmentBody(id=789)

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.content = b"fake-pdf-binary-content"
    mock_resp.headers = {"content-type": "application/octet-stream"}

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_resp):
        response = download_attachment.sync_detailed(
            client=api_client,
            body=body,
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, File)
    assert response.parsed.payload.read() == b"fake-pdf-binary-content"


def test_get_linehauls(api_client, mock_response):
    response_data = {
        "status": "success",
        "code": 1302,
        "message": "Linehauls found",
        "linehauls": [{"id": "40002135_DC-DDI", "shipments": 323}],
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(200, response_data)):
        response = get_linehauls.sync_detailed(
            client=api_client,
            client_header=123,
            apikey="test-key",
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, GetLinehaulsResponse200)
    assert response.parsed.status == "success"
    assert response.parsed.code == 1302
    assert response.parsed.message == "Linehauls found"
    assert isinstance(response.parsed.linehauls, list)
    assert len(response.parsed.linehauls) == 1
    assert response.parsed.linehauls[0].id == "40002135_DC-DDI"
    assert response.parsed.linehauls[0].shipments == 323


def test_close_linehaul(api_client, mock_response):
    body = CloseLinehaulBody(
        linehaul_id="40002135_DC-DDI",
        container_type="PLL",
        container_amount=5,
        container_length=120.0,
        container_width=80.0,
        container_height=100.0,
        address=CloseLinehaulBodyAddress(
            name="Depot Amsterdam",
            street="Depotweg",
            house_nr="1",
            postcode="1000AA",
            city="Amsterdam",
            country="NL",
        ),
    )

    response_data = {
        "status": "success",
        "code": 1306,
        "message": "Linehaul closed",
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(200, response_data)):
        response = close_linehaul.sync_detailed(
            client=api_client,
            client_header=123,
            apikey="test-key",
            body=body,
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, CloseLinehaulResponse200)
    assert response.parsed.status == "success"
    assert response.parsed.code == 1306
    assert response.parsed.message == "Linehaul closed"


def test_update_routes(api_client, mock_response):
    body = UpdateRoutesBody(
        filter_=UpdateRoutesBodyFilter(
            carrier=123,
            service=456,
            country="NL",
            day=1,
            time_from="08:00",
            time_to="18:00",
        ),
        adjustment=UpdateRoutesBodyAdjustment(
            capacity=20.0,
            capacity_cbm=0.75,
        ),
        test=True,
    )

    response_data = {
        "status": "success",
        "code": 1801,
        "message": "Routes updated",
    }

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_response(200, response_data)):
        response = update_routes.sync_detailed(
            client=api_client,
            client_header=123,
            apikey="test-key",
            body=body,
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, UpdateRoutesResponse200)
    assert response.parsed.status == "success"
    assert response.parsed.code == 1801
    assert response.parsed.message == "Routes updated"


def test_test_api_connection(api_client):
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.content = b"OK"
    mock_resp.headers = {"content-type": "application/octet-stream"}

    with patch.object(api_client.get_httpx_client(), 'request', return_value=mock_resp):
        response = test_api_connection.sync_detailed(
            client=api_client,
            client_header=123,
            apikey="test-key",
        )

    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.parsed, File)
    assert response.parsed.payload.read() == b"OK"
