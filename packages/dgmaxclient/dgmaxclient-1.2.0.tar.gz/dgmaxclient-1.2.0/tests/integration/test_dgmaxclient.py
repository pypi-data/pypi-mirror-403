from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

from dgmaxclient import DGMaxClient, ElectronicDocument


def test_list_companies(client: DGMaxClient):
    companies = client.companies.list()
    for company in companies.results:
        print(f"{company.name} ({company.rnc})")


@pytest.mark.manual
def test_create_fiscal_invoice(client: DGMaxClient, company_id: str):
    fiscal_invoice_data = {
        "company": {"id": company_id},
        "ecf": {
            "encabezado": {
                "version": "1.0",
                "id_doc": {
                    "tipo_ecf": 31,
                    "e_ncf": "E310000910256",
                    "fecha_vencimiento_secuencia": "31-12-2028",
                    "indicador_monto_gravado": 0,
                    "tipo_ingresos": "01",
                    "tipo_pago": 1,
                },
                "emisor": {
                    "rnc_emisor": "132786262",
                    "razon_social_emisor": "CloudYA SRL",
                    "direccion_emisor": "Carretera Mella No. 1",
                    "fecha_emision": "13-01-2025",
                },
                "comprador": {
                    "rnc_comprador": "130952027",
                    "razon_social_comprador": "Paul Hoffman",
                    "correo_comprador": "paul@hoffman.com",
                },
                "totales": {
                    "monto_gravado_total": "2000.00",
                    "monto_gravado_i1": "2000.00",
                    "itbis1": "18",
                    "total_itbis": "360.00",
                    "total_itbis1": "360.00",
                    "monto_total": "2360.00",
                },
            },
            "detalles_items": {
                "item": [
                    {
                        "numero_linea": "1",
                        "indicador_facturacion": 1,
                        "nombre_item": "Zapato super soccer",
                        "indicador_bien_o_servicio": 1,
                        "cantidad_item": "1",
                        "unidad_medida": 43,
                        "precio_unitario_item": "1000.00",
                        "monto_item": "1000.00",
                    },
                    {
                        "numero_linea": "2",
                        "indicador_facturacion": 1,
                        "nombre_item": "Media corona no. 16",
                        "indicador_bien_o_servicio": 1,
                        "cantidad_item": "10",
                        "unidad_medida": 32,
                        "precio_unitario_item": "100.00",
                        "monto_item": "1000.00",
                    },
                ]
            },
        },
    }

    try:
        fiscal_invoice = client.fiscal_invoices.create(fiscal_invoice_data)
    except Exception as e:
        print(e)

    print(f"Invoice created: {fiscal_invoice.encf}")
    print(f"Status: {fiscal_invoice.status}")


def test_get_invoice(client: DGMaxClient):
    invoice: ElectronicDocument = client.invoices.get(
        "0693c462-a105-7d58-8000-60529057063c"
    )
    print(invoice)


@pytest.mark.manual
def test_create_fiscal_invoices_parallel(client: DGMaxClient, company_id: str):
    """Exhaustion test: create 10 fiscal invoices in parallel (910256 -> 910265)."""
    START_SEQ = int(os.environ.get("START_SEQ", 255))
    COUNT = 10
    MAX_WORKERS = 2  # Adjust based on API rate limits

    def build_invoice_data(sequence_number: int) -> dict:
        """Build fiscal invoice data with unique e_ncf sequence."""
        return {
            "company": {"id": company_id},
            "ecf": {
                "encabezado": {
                    "version": "1.0",
                    "id_doc": {
                        "tipo_ecf": 31,
                        "e_ncf": f"E31{sequence_number:010d}",
                        "fecha_vencimiento_secuencia": "31-12-2028",
                        "indicador_monto_gravado": 0,
                        "tipo_ingresos": "01",
                        "tipo_pago": 1,
                    },
                    "emisor": {
                        "rnc_emisor": "132786262",
                        "razon_social_emisor": "CloudYA SRL",
                        "direccion_emisor": "Carretera Mella No. 1",
                        "fecha_emision": "13-01-2025",
                    },
                    "comprador": {
                        "rnc_comprador": "130952027",
                        "razon_social_comprador": "Paul Hoffman",
                        "correo_comprador": "paul@hoffman.com",
                    },
                    "totales": {
                        "monto_gravado_total": "2000.00",
                        "monto_gravado_i1": "2000.00",
                        "itbis1": "18",
                        "total_itbis": "360.00",
                        "total_itbis1": "360.00",
                        "monto_total": "2360.00",
                    },
                },
                "detalles_items": {
                    "item": [
                        {
                            "numero_linea": "1",
                            "indicador_facturacion": 1,
                            "nombre_item": "Zapato super soccer",
                            "indicador_bien_o_servicio": 1,
                            "cantidad_item": "1",
                            "unidad_medida": 43,
                            "precio_unitario_item": "1000.00",
                            "monto_item": "1000.00",
                        },
                        {
                            "numero_linea": "2",
                            "indicador_facturacion": 1,
                            "nombre_item": "Media corona no. 16",
                            "indicador_bien_o_servicio": 1,
                            "cantidad_item": "10",
                            "unidad_medida": 32,
                            "precio_unitario_item": "100.00",
                            "monto_item": "1000.00",
                        },
                    ]
                },
            },
        }

    def submit_invoice(seq: int):
        """Submit a single invoice and return result with timing."""
        data = build_invoice_data(seq)
        start = time.perf_counter()
        invoice = client.fiscal_invoices.create(data)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return seq, invoice, elapsed_ms

    results = {}
    errors = {}
    timings = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(submit_invoice, seq): seq
            for seq in range(START_SEQ, START_SEQ + COUNT)
        }

        for future in as_completed(futures):
            seq = futures[future]
            try:
                seq_num, invoice, elapsed_ms = future.result()
                results[seq_num] = invoice
                timings.append(elapsed_ms)
                print(f"✓ {invoice.encf} - {invoice.status} [{elapsed_ms:.0f}ms]")
            except Exception as e:
                errors[seq] = str(e)
                print(f"✗ E310000{seq} - {e}")

    # Print timing summary
    if timings:
        avg_ms = sum(timings) / len(timings)
        min_ms = min(timings)
        max_ms = max(timings)
        print(f"\n{'─' * 50}")
        print(f"Timing: avg={avg_ms:.0f}ms | min={min_ms:.0f}ms | max={max_ms:.0f}ms")

    print(f"Results: {len(results)} success, {len(errors)} failed")
    assert len(errors) == 0, f"Failed invoices: {errors}"


@pytest.mark.manual
def test_create_invoice(client: DGMaxClient, company_id: str):
    """Create a single invoice (E32) - sync since amount < 250k."""
    invoice_data = {
        "company": {"id": company_id},
        "ecf": {
            "encabezado": {
                "id_doc": {
                    "tipo_ecf": 32,
                    "e_ncf": "E320000100001",
                    "fecha_vencimiento_secuencia": "31-12-2026",
                    "indicador_monto_gravado": 1,
                    "tipo_ingresos": "01",
                    "tipo_pago": 1,
                },
                "emisor": {
                    "rnc_emisor": "132786262",
                    "razon_social_emisor": "CloudYA SRL",
                    "direccion_emisor": "Carretera Mella No. 1",
                    "fecha_emision": "13-01-2025",
                },
                "comprador": {
                    "rnc_comprador": "130952027",
                    "razon_social_comprador": "Paul Hoffman",
                },
                "totales": {
                    "monto_gravado_total": "1500.00",
                    "monto_gravado_i3": "1500.00",
                    "itbis3": "0",
                    "total_itbis": "0",
                    "total_itbis3": "0",
                    "monto_total": "1500.00",
                },
            },
            "detalles_items": {
                "item": [
                    {
                        "numero_linea": "1",
                        "indicador_facturacion": 1,
                        "nombre_item": "Resma papel bond carta 500 hojas",
                        "indicador_bien_o_servicio": 1,
                        "cantidad_item": "5",
                        "precio_unitario_item": "300.00",
                        "monto_item": "1500.00",
                    }
                ]
            },
        },
    }

    try:
        invoice = client.invoices.create(invoice_data)
    except Exception as e:
        print(e)
        raise

    print(f"Invoice created: {invoice.encf}")
    print(f"Status: {invoice.status}")


@pytest.mark.manual
def test_create_invoices_parallel(client: DGMaxClient, company_id: str):
    """Exhaustion test: create 10 E32 invoices in parallel (sync, < 250k)."""
    START_SEQ = 910325
    COUNT = 10
    MAX_WORKERS = 2  # Adjust based on API rate limits

    def build_invoice_data(sequence_number: int) -> dict:
        """Build invoice data with unique e_ncf sequence."""
        return {
            "company": {"id": company_id},
            "ecf": {
                "encabezado": {
                    "id_doc": {
                        "tipo_ecf": 32,
                        "e_ncf": f"E32{sequence_number:010d}",
                        "fecha_vencimiento_secuencia": "31-12-2026",
                        "indicador_monto_gravado": 1,
                        "tipo_ingresos": "01",
                        "tipo_pago": 1,
                    },
                    "emisor": {
                        "rnc_emisor": "132786262",
                        "razon_social_emisor": "CloudYA SRL",
                        "direccion_emisor": "Carretera Mella No. 1",
                        "fecha_emision": "13-01-2025",
                    },
                    "comprador": {
                        "rnc_comprador": "130952027",
                        "razon_social_comprador": "Paul Hoffman",
                    },
                    "totales": {
                        "monto_gravado_total": "1500.00",
                        "monto_gravado_i3": "1500.00",
                        "itbis3": "0",
                        "total_itbis": "0",
                        "total_itbis3": "0",
                        "monto_total": "1500.00",
                    },
                },
                "detalles_items": {
                    "item": [
                        {
                            "numero_linea": "1",
                            "indicador_facturacion": 1,
                            "nombre_item": "Resma papel bond carta 500 hojas",
                            "indicador_bien_o_servicio": 1,
                            "cantidad_item": "5",
                            "precio_unitario_item": "300.00",
                            "monto_item": "1500.00",
                        }
                    ]
                },
            },
        }

    def submit_invoice(seq: int):
        """Submit a single invoice and return result with timing."""
        data = build_invoice_data(seq)
        start = time.perf_counter()
        invoice = client.invoices.create(data)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return seq, invoice, elapsed_ms

    results = {}
    errors = {}
    timings = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(submit_invoice, seq): seq
            for seq in range(START_SEQ, START_SEQ + COUNT)
        }

        for future in as_completed(futures):
            seq = futures[future]
            try:
                seq_num, invoice, elapsed_ms = future.result()
                results[seq_num] = invoice
                timings.append(elapsed_ms)
                print(f"✓ {invoice.encf} - {invoice.status} [{elapsed_ms:.0f}ms]")
            except Exception as e:
                errors[seq] = str(e)
                print(f"✗ E320000{seq} - {e}")

    # Print timing summary
    if timings:
        avg_ms = sum(timings) / len(timings)
        min_ms = min(timings)
        max_ms = max(timings)
        print(f"\n{'─' * 50}")
        print(f"Timing: avg={avg_ms:.0f}ms | min={min_ms:.0f}ms | max={max_ms:.0f}ms")

    print(f"Results: {len(results)} success, {len(errors)} failed")
    assert len(errors) == 0, f"Failed invoices: {errors}"
