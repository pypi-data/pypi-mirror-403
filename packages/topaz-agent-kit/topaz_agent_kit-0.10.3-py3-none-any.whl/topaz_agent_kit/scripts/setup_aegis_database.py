#!/usr/bin/env python3
"""Setup script for Aegis pipeline.

Creates SQLite database, initializes schema, and generates mock data:
- ERP system data (vendors, POs, payment history)
- Contract management (SOWs, rate cards, commercial terms)
- Project tracking (projects, WBS, milestones)
- Policy & controls (evidence requirements, exception rules, anomaly thresholds)
- Invoice & evidence PDF files with exception scenarios
- Ground truth labels for validation

Usage:
    python scripts/setup_aegis_database.py [--db-path <path>] [--output-dir <dir>] [--reset]
    uv run -m scripts.setup_aegis_database --db-path projects/pa/data/aegis/aegis_database.db --reset
"""

import sqlite3
import os
import sys
import argparse
import random
import uuid
import json
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from rich.console import Console
    from rich.table import Table as RichTable
    from rich.panel import Panel
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Define dummy classes for type hints if Rich is not available
    RichTable = None
    Console = None
    Panel = None
    box = None

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from topaz_agent_kit.utils.path_resolver import resolve_script_path, detect_project_name

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not available. PDF generation will be skipped.")
    print("Install with: pip install reportlab")


# ============================================================================
# Multi-Language Support
# ============================================================================

# Supported languages: Configurable distribution (default: 40% English, 60% non-English, randomly selected)
SUPPORTED_LANGUAGES = {
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "pl": "Polish",
    "hu": "Hungarian",
    "ro": "Romanian",
    "bg": "Bulgarian",
    "sv": "Swedish",
    "tr": "Turkish",
    "zh": "Mandarin",
    "id": "Indonesian",
    "ms": "Malay"
}

NON_ENGLISH_LANGUAGES = ["de", "fr", "es", "it", "pt", "pl", "hu", "ro", "bg", "sv", "tr", "zh", "id", "ms"]

# Language templates for common terms
LANGUAGE_TEMPLATES = {
    "en": {
        "invoice": "Invoice",
        "invoice_number": "Invoice Number",
        "invoice_date": "Invoice Date",
        "due_date": "Due Date",
        "vendor": "Vendor",
        "total_amount": "Total Amount",
        "line_items": "Line Items",
        "description": "Description",
        "quantity": "Quantity",
        "unit_price": "Unit Price",
        "total": "Total",
        "retention": "Retention",
        "retention_percentage": "Retention Percentage",
        "retention_applied": "Retention Applied",
        "liquidated_damages": "Liquidated Damages",
        "ld_applicable": "LD Applicable",
        "ld_amount": "LD Amount",
        "ld_applied": "LD Applied",
        "evidence_references": "Supporting Documents",
        "po_reference": "PO Reference",
        "sow_reference": "SOW Reference",
        "project_reference": "Project Reference",
        "wbs_reference": "WBS Reference",
        "subtotal": "Subtotal",
        "tax": "Tax",
        "payment_terms": "Payment Terms",
        "payment_terms_text": "Payment Terms: Net 30",
        "questions": "Questions?",
        "contact_us": "Contact us at accounts@vendor.com or (713) 555-0100",
        "thank_you": "Thank you for your business!",
        "note_process_payment": "Note: Please process payment within terms. Contact for questions.",
        "service_item": "Service Item",
        "timesheet": "Timesheet",
        "completion_certificate": "Completion Certificate",
        "grn": "Goods Receipt Note",
        "grn_number": "GRN Number:",
        "grn_date": "GRN Date:",
        "delivery_date": "Delivery Date:",
        "material_code": "Material Code:",
        "material_description": "Material Description:",
        "unit_of_measure": "Unit of Measure:",
        "received_quantity": "Received Quantity:",
        "received_by": "Received By:",
        "receipt_confirmed": "Receipt Confirmed",
        "worker_name": "Worker Name:",
        "employee_id": "Employee ID:",
        "coverage_period": "Coverage Period:",
        "total_hours_worked": "Total Hours Worked:",
        "invoice_reference": "Invoice Reference:",
        "project": "Project:",
        "date": "Date",
        "start": "Start",
        "end": "End",
        "hours": "Hours",
        "task": "Task",
        "location": "Location",
        "task_description": "Task Description",
        "time": "Time",
        "activity": "Activity",
        "status": "Status",
        "operator": "Operator",
        "operator_signature": "Operator Signature:",
        "worker_signature": "Worker Signature:",
        "supervisor_approval": "Supervisor Approval:",
        "approved_by": "Approved By:",
        "work_description": "Work Description:",
        "completion_date": "Completion Date:",
        "vessel_name": "Vessel Name:",
        "log_date": "Log Date:",
        "hours_operated": "Hours Operated:",
        "equipment_id": "Equipment ID:",
        "hours_used": "Hours Used:",
        "certify_intro": "This is to certify that",
        "certify_completion": "has been completed in accordance with the contract requirements.",
        "title": "Title:",
        "signature": "Signature:",
        "captain_signature": "Captain Signature:",
        "imo_number": "IMO Number:",
        "flag_state": "Flag State:",
        "distance": "Distance",
        "project_code": "Project Code:",
        "work_order": "Work Order:",
        "contract_number": "Contract Number:",
        "quality_check": "Quality Check:",
        "safety_compliance": "Safety Compliance:",
        "equipment_type": "Equipment Type:",
        "serial_number": "Serial Number:",
        "project_site": "Project Site:",
        "bill_to": "Bill To:",
        "phone": "Phone:",
        "email": "Email:",
        "item_code": "Item Code",
        "po_line_reference": "PO Line",
        "work_completed_per_sow": "Work completed per SOW {sow_reference}",
        "project_manager": "Project Manager",
        "passed": "Passed",
        "verified": "Verified"
    },
    "de": {
        "invoice": "Rechnung",
        "invoice_number": "Rechnungsnummer",
        "invoice_date": "Rechnungsdatum",
        "due_date": "Fälligkeitsdatum",
        "vendor": "Lieferant",
        "total_amount": "Gesamtbetrag",
        "line_items": "Positionen",
        "description": "Beschreibung",
        "quantity": "Menge",
        "unit_price": "Einzelpreis",
        "total": "Gesamt",
        "retention": "Einbehalt",
        "retention_percentage": "Einbehaltsprozentsatz",
        "retention_applied": "Einbehalt Angewendet",
        "liquidated_damages": "Vertragsstrafe",
        "ld_applicable": "VS Anwendbar",
        "ld_amount": "VS Betrag",
        "ld_applied": "VS Angewendet",
        "evidence_references": "Belegdokumente",
        "po_reference": "Bestellnummer",
        "sow_reference": "SOW Referenz",
        "project_reference": "Projektreferenz",
        "wbs_reference": "WBS Referenz",
        "subtotal": "Zwischensumme",
        "tax": "Steuer",
        "payment_terms": "Zahlungsbedingungen",
        "payment_terms_text": "Zahlungsbedingungen: Netto 30",
        "questions": "Fragen?",
        "contact_us": "Kontaktieren Sie uns unter accounts@vendor.com oder (713) 555-0100",
        "thank_you": "Vielen Dank für Ihr Geschäft!",
        "note_process_payment": "Hinweis: Bitte bearbeiten Sie die Zahlung innerhalb der Fristen. Kontakt bei Fragen.",
        "service_item": "Serviceartikel",
        "timesheet": "Stundenzettel",
        "completion_certificate": "Fertigstellungsbescheinigung",
        "grn": "Wareneingangsbestätigung",
        "grn_number": "GRN-Nummer:",
        "grn_date": "GRN-Datum:",
        "delivery_date": "Lieferdatum:",
        "material_code": "Materialcode:",
        "material_description": "Materialbeschreibung:",
        "unit_of_measure": "Mengeneinheit:",
        "received_quantity": "Empfangene Menge:",
        "received_by": "Empfangen von:",
        "receipt_confirmed": "Empfang bestätigt",
        "worker_name": "Arbeitername:",
        "employee_id": "Mitarbeiter-ID:",
        "coverage_period": "Abdeckungszeitraum:",
        "total_hours_worked": "Gesamtarbeitsstunden:",
        "invoice_reference": "Rechnungsreferenz:",
        "project": "Projekt:",
        "date": "Datum",
        "start": "Start",
        "end": "Ende",
        "hours": "Stunden",
        "task": "Aufgabe",
        "location": "Standort",
        "task_description": "Aufgabenbeschreibung",
        "time": "Zeit",
        "activity": "Aktivität",
        "status": "Status",
        "operator": "Bedienungspersonal",
        "operator_signature": "Unterschrift Bedienungspersonal:",
        "worker_signature": "Arbeitnehmer-Unterschrift:",
        "supervisor_approval": "Vorgesetzten-Genehmigung:",
        "approved_by": "Genehmigt von:",
        "work_description": "Arbeitsbeschreibung:",
        "completion_date": "Fertigstellungsdatum:",
        "vessel_name": "Schiffsname:",
        "log_date": "Protokolldatum:",
        "hours_operated": "Betriebsstunden:",
        "equipment_id": "Geräte-ID:",
        "hours_used": "Verwendete Stunden:",
        "certify_intro": "Hiermit wird bescheinigt, dass",
        "certify_completion": "in Übereinstimmung mit den Vertragsbestimmungen abgeschlossen wurde.",
        "title": "Titel:",
        "signature": "Unterschrift:",
        "captain_signature": "Kapitänsunterschrift:",
        "imo_number": "IMO-Nummer:",
        "flag_state": "Flaggenstaat:",
        "distance": "Distanz",
        "project_code": "Projektcode:",
        "work_order": "Arbeitsauftrag:",
        "contract_number": "Vertragsnummer:",
        "quality_check": "Qualitätsprüfung:",
        "safety_compliance": "Sicherheitskonformität:",
        "equipment_type": "Gerätetyp:",
        "serial_number": "Seriennummer:",
        "project_site": "Projektstandort:",
        "bill_to": "Rechnung an:",
        "phone": "Telefon:",
        "email": "E-Mail:",
        "item_code": "Artikelcode",
        "po_line_reference": "PO-Position",
        "work_completed_per_sow": "Arbeit abgeschlossen gemäß SOW {sow_reference}",
        "project_manager": "Projektmanager",
        "passed": "Bestanden",
        "verified": "Verifiziert"
    },
    "fr": {
        "invoice": "Facture",
        "invoice_number": "Numéro de facture",
        "invoice_date": "Date de facture",
        "due_date": "Date d'échéance",
        "vendor": "Fournisseur",
        "total_amount": "Montant total",
        "line_items": "Articles",
        "description": "Description",
        "quantity": "Quantité",
        "unit_price": "Prix unitaire",
        "total": "Total",
        "retention": "Rétention",
        "retention_percentage": "Pourcentage de rétention",
        "retention_applied": "Rétention appliquée",
        "liquidated_damages": "Dommages-intérêts",
        "ld_applicable": "DI Applicable",
        "ld_amount": "Montant DI",
        "ld_applied": "DI Appliqué",
        "evidence_references": "Documents justificatifs",
        "po_reference": "Référence PO",
        "sow_reference": "Référence SOW",
        "project_reference": "Référence projet",
        "wbs_reference": "Référence WBS",
        "subtotal": "Sous-total",
        "tax": "Taxe",
        "payment_terms": "Conditions de paiement",
        "payment_terms_text": "Conditions de paiement: Net 30",
        "questions": "Des questions?",
        "contact_us": "Contactez-nous à accounts@vendor.com ou (713) 555-0100",
        "thank_you": "Merci pour votre activité!",
        "note_process_payment": "Note: Veuillez traiter le paiement dans les délais. Contactez-nous pour toute question.",
        "service_item": "Article de service",
        "timesheet": "Feuille de temps",
        "completion_certificate": "Certificat de finition",
        "grn": "Bon de réception",
        "grn_number": "Numéro GRN:",
        "grn_date": "Date GRN:",
        "delivery_date": "Date de livraison:",
        "material_code": "Code matériau:",
        "material_description": "Description du matériau:",
        "unit_of_measure": "Unité de mesure:",
        "received_quantity": "Quantité reçue:",
        "received_by": "Reçu par:",
        "receipt_confirmed": "Réception confirmée",
        "worker_name": "Nom du travailleur:",
        "employee_id": "ID employé:",
        "coverage_period": "Période de couverture:",
        "total_hours_worked": "Total heures travaillées:",
        "invoice_reference": "Référence facture:",
        "project": "Projet:",
        "date": "Date",
        "start": "Début",
        "end": "Fin",
        "hours": "Heures",
        "task": "Tâche",
        "location": "Emplacement",
        "task_description": "Description de la tâche",
        "time": "Heure",
        "activity": "Activité",
        "status": "Statut",
        "operator": "Opérateur",
        "operator_signature": "Signature opérateur:",
        "worker_signature": "Signature travailleur:",
        "supervisor_approval": "Approbation superviseur:",
        "approved_by": "Approuvé par:",
        "work_description": "Description du travail:",
        "completion_date": "Date d'achèvement:",
        "vessel_name": "Nom du navire:",
        "log_date": "Date du journal:",
        "hours_operated": "Heures d'exploitation:",
        "equipment_id": "ID équipement:",
        "hours_used": "Heures utilisées:",
        "certify_intro": "Il est certifié que",
        "certify_completion": "a été complété conformément aux exigences du contrat.",
        "title": "Titre:",
        "signature": "Signature:",
        "captain_signature": "Signature du capitaine:",
        "imo_number": "Numéro OMI:",
        "flag_state": "Pavillon:",
        "distance": "Distance",
        "project_code": "Code projet:",
        "work_order": "Ordre de travail:",
        "contract_number": "Numéro de contrat:",
        "quality_check": "Contrôle qualité:",
        "safety_compliance": "Conformité sécurité:",
        "equipment_type": "Type d'équipement:",
        "serial_number": "Numéro de série:",
        "project_site": "Site du projet:",
        "bill_to": "Facturer à:",
        "phone": "Téléphone:",
        "email": "Courriel:",
        "item_code": "Code article",
        "po_line_reference": "Ligne PO",
        "work_completed_per_sow": "Travail terminé selon SOW {sow_reference}",
        "project_manager": "Chef de projet",
        "passed": "Réussi",
        "verified": "Vérifié"
    },
    "es": {
        "invoice": "Factura",
        "invoice_number": "Número de factura",
        "invoice_date": "Fecha de factura",
        "due_date": "Fecha de vencimiento",
        "vendor": "Proveedor",
        "total_amount": "Importe total",
        "line_items": "Artículos",
        "description": "Descripción",
        "quantity": "Cantidad",
        "unit_price": "Precio unitario",
        "total": "Total",
        "retention": "Retención",
        "retention_percentage": "Porcentaje de retención",
        "retention_applied": "Retención aplicada",
        "liquidated_damages": "Daños y perjuicios",
        "ld_applicable": "DP Aplicable",
        "ld_amount": "Importe DP",
        "ld_applied": "DP Aplicado",
        "evidence_references": "Documentos de respaldo",
        "po_reference": "Referencia PO",
        "sow_reference": "Referencia SOW",
        "project_reference": "Referencia del proyecto",
        "wbs_reference": "Referencia WBS",
        "subtotal": "Subtotal",
        "tax": "Impuesto",
        "payment_terms": "Términos de pago",
        "payment_terms_text": "Términos de pago: Neto 30",
        "questions": "¿Preguntas?",
        "contact_us": "Contáctenos en accounts@vendor.com o (713) 555-0100",
        "thank_you": "¡Gracias por su negocio!",
        "note_process_payment": "Nota: Por favor procese el pago dentro de los términos. Contáctenos para preguntas.",
        "service_item": "Artículo de servicio",
        "timesheet": "Hoja de tiempo",
        "completion_certificate": "Certificado de finalización",
        "grn": "Nota de Recepción de Mercancías",
        "grn_number": "Número GRN:",
        "grn_date": "Fecha GRN:",
        "delivery_date": "Fecha de entrega:",
        "material_code": "Código de material:",
        "material_description": "Descripción del material:",
        "unit_of_measure": "Unidad de medida:",
        "received_quantity": "Cantidad recibida:",
        "received_by": "Recibido por:",
        "receipt_confirmed": "Recepción confirmada",
        "worker_name": "Nombre del trabajador:",
        "employee_id": "ID de empleado:",
        "coverage_period": "Período de cobertura:",
        "total_hours_worked": "Total horas trabajadas:",
        "invoice_reference": "Referencia de factura:",
        "project": "Proyecto:",
        "date": "Fecha",
        "start": "Inicio",
        "end": "Fin",
        "hours": "Horas",
        "task": "Tarea",
        "location": "Ubicación",
        "task_description": "Descripción de la tarea",
        "time": "Hora",
        "activity": "Actividad",
        "status": "Estado",
        "operator": "Operador",
        "operator_signature": "Firma del operador:",
        "worker_signature": "Firma del trabajador:",
        "supervisor_approval": "Aprobación del supervisor:",
        "approved_by": "Aprobado por:",
        "work_description": "Descripción del trabajo:",
        "completion_date": "Fecha de finalización:",
        "vessel_name": "Nombre de la embarcación:",
        "log_date": "Fecha del registro:",
        "hours_operated": "Horas operadas:",
        "equipment_id": "ID del equipo:",
        "hours_used": "Horas utilizadas:",
        "certify_intro": "Se certifica que",
        "certify_completion": "ha sido completado de acuerdo con los requisitos del contrato.",
        "title": "Título:",
        "signature": "Firma:",
        "captain_signature": "Firma del capitán:",
        "imo_number": "Número OMI:",
        "flag_state": "Bandera:",
        "distance": "Distancia",
        "project_code": "Código del proyecto:",
        "work_order": "Orden de trabajo:",
        "contract_number": "Número de contrato:",
        "quality_check": "Control de calidad:",
        "safety_compliance": "Cumplimiento de seguridad:",
        "equipment_type": "Tipo de equipo:",
        "serial_number": "Número de serie:",
        "project_site": "Sitio del proyecto:",
        "bill_to": "Facturar a:",
        "phone": "Teléfono:",
        "email": "Correo electrónico:",
        "item_code": "Código de artículo",
        "po_line_reference": "Línea PO",
        "work_completed_per_sow": "Trabajo completado según SOW {sow_reference}",
        "project_manager": "Gerente de proyecto",
        "passed": "Aprobado",
        "verified": "Verificado"
    },
    "it": {
        "invoice": "Fattura",
        "invoice_number": "Numero fattura",
        "invoice_date": "Data fattura",
        "due_date": "Data scadenza",
        "vendor": "Fornitore",
        "total_amount": "Importo totale",
        "line_items": "Voci",
        "description": "Descrizione",
        "quantity": "Quantità",
        "unit_price": "Prezzo unitario",
        "total": "Totale",
        "retention": "Ritenuta",
        "retention_percentage": "Percentuale di ritenuta",
        "retention_applied": "Ritenuta applicata",
        "liquidated_damages": "Penali",
        "ld_applicable": "Penali Applicabili",
        "ld_amount": "Importo penali",
        "ld_applied": "Penali Applicate",
        "evidence_references": "Documenti di supporto",
        "po_reference": "Riferimento PO",
        "sow_reference": "Riferimento SOW",
        "project_reference": "Riferimento progetto",
        "wbs_reference": "Riferimento WBS",
        "subtotal": "Subtotale",
        "tax": "Imposta",
        "payment_terms": "Termini di pagamento",
        "payment_terms_text": "Termini di pagamento: Netto 30",
        "questions": "Domande?",
        "contact_us": "Contattaci a accounts@vendor.com o (713) 555-0100",
        "thank_you": "Grazie per il tuo business!",
        "note_process_payment": "Nota: Si prega di elaborare il pagamento entro i termini. Contattaci per domande.",
        "service_item": "Articolo di servizio",
        "timesheet": "Foglio presenze",
        "completion_certificate": "Certificato di completamento",
        "grn": "Nota di Ricevimento Merci",
        "grn_number": "Numero GRN:",
        "grn_date": "Data GRN:",
        "delivery_date": "Data di consegna:",
        "material_code": "Codice materiale:",
        "material_description": "Descrizione materiale:",
        "unit_of_measure": "Unità di misura:",
        "received_quantity": "Quantità ricevuta:",
        "received_by": "Ricevuto da:",
        "receipt_confirmed": "Ricevuta confermata",
        "worker_name": "Nome lavoratore:",
        "employee_id": "ID dipendente:",
        "coverage_period": "Periodo di copertura:",
        "total_hours_worked": "Totale ore lavorate:",
        "invoice_reference": "Riferimento fattura:",
        "project": "Progetto:",
        "date": "Data",
        "start": "Inizio",
        "end": "Fine",
        "hours": "Ore",
        "task": "Compito",
        "location": "Posizione",
        "task_description": "Descrizione compito",
        "time": "Ora",
        "activity": "Attività",
        "status": "Stato",
        "operator": "Operatore",
        "operator_signature": "Firma operatore:",
        "worker_signature": "Firma lavoratore:",
        "supervisor_approval": "Approvazione supervisore:",
        "approved_by": "Approvato da:",
        "work_description": "Descrizione lavoro:",
        "completion_date": "Data completamento:",
        "vessel_name": "Nome nave:",
        "log_date": "Data registro:",
        "hours_operated": "Ore di funzionamento:",
        "equipment_id": "ID attrezzatura:",
        "hours_used": "Ore utilizzate:",
        "certify_intro": "Si certifica che",
        "certify_completion": "è stato completato in conformità con i requisiti del contratto.",
        "title": "Titolo:",
        "signature": "Firma:",
        "captain_signature": "Firma del capitano:",
        "imo_number": "Numero IMO:",
        "flag_state": "Bandiera:",
        "distance": "Distanza",
        "project_code": "Codice progetto:",
        "work_order": "Ordine di lavoro:",
        "contract_number": "Numero contratto:",
        "quality_check": "Controllo qualità:",
        "safety_compliance": "Conformità sicurezza:",
        "equipment_type": "Tipo attrezzatura:",
        "serial_number": "Numero di serie:",
        "project_site": "Sito progetto:",
        "bill_to": "Fatturare a:",
        "phone": "Telefono:",
        "email": "Email:",
        "item_code": "Codice articolo",
        "po_line_reference": "Riga PO",
        "work_completed_per_sow": "Lavoro completato secondo SOW {sow_reference}",
        "project_manager": "Project Manager",
        "passed": "Superato",
        "verified": "Verificato"
    },
    "pt": {
        "invoice": "Fatura",
        "invoice_number": "Número da fatura",
        "invoice_date": "Data da fatura",
        "due_date": "Data de vencimento",
        "vendor": "Fornecedor",
        "total_amount": "Valor total",
        "line_items": "Itens",
        "description": "Descrição",
        "quantity": "Quantidade",
        "unit_price": "Preço unitário",
        "total": "Total",
        "retention": "Retenção",
        "retention_percentage": "Percentual de retenção",
        "retention_applied": "Retenção aplicada",
        "liquidated_damages": "Multa contratual",
        "ld_applicable": "MC Aplicável",
        "ld_amount": "Valor MC",
        "ld_applied": "MC Aplicada",
        "evidence_references": "Documentos de apoio",
        "po_reference": "Referência PO",
        "sow_reference": "Referência SOW",
        "project_reference": "Referência do projeto",
        "wbs_reference": "Referência WBS",
        "subtotal": "Subtotal",
        "tax": "Imposto",
        "payment_terms": "Termos de pagamento",
        "payment_terms_text": "Termos de pagamento: Líquido 30",
        "questions": "Perguntas?",
        "contact_us": "Entre em contato conosco em accounts@vendor.com ou (713) 555-0100",
        "thank_you": "Obrigado pelo seu negócio!",
        "note_process_payment": "Nota: Por favor, processe o pagamento dentro dos termos. Entre em contato para perguntas.",
        "service_item": "Item de serviço",
        "timesheet": "Folha de ponto",
        "completion_certificate": "Certificado de conclusão",
        "grn": "Nota de Recebimento de Mercadorias",
        "grn_number": "Número GRN:",
        "grn_date": "Data GRN:",
        "delivery_date": "Data de entrega:",
        "material_code": "Código do material:",
        "material_description": "Descrição do material:",
        "unit_of_measure": "Unidade de medida:",
        "received_quantity": "Quantidade recebida:",
        "received_by": "Recebido por:",
        "receipt_confirmed": "Recebimento confirmado",
        "worker_name": "Nome do trabalhador:",
        "employee_id": "ID do funcionário:",
        "coverage_period": "Período de cobertura:",
        "total_hours_worked": "Total de horas trabalhadas:",
        "invoice_reference": "Referência da fatura:",
        "project": "Projeto:",
        "date": "Data",
        "start": "Início",
        "end": "Fim",
        "hours": "Horas",
        "task": "Tarefa",
        "location": "Localização",
        "task_description": "Descrição da tarefa",
        "time": "Hora",
        "activity": "Atividade",
        "status": "Status",
        "operator": "Operador",
        "operator_signature": "Assinatura do operador:",
        "worker_signature": "Assinatura do trabalhador:",
        "supervisor_approval": "Aprovação do supervisor:",
        "approved_by": "Aprovado por:",
        "work_description": "Descrição do trabalho:",
        "completion_date": "Data de conclusão:",
        "vessel_name": "Nome da embarcação:",
        "log_date": "Data do registro:",
        "hours_operated": "Horas operadas:",
        "equipment_id": "ID do equipamento:",
        "hours_used": "Horas utilizadas:",
        "certify_intro": "Certifica-se que",
        "certify_completion": "foi concluído de acordo com os requisitos do contrato.",
        "title": "Título:",
        "signature": "Assinatura:",
        "captain_signature": "Assinatura do capitão:",
        "imo_number": "Número IMO:",
        "flag_state": "Bandeira:",
        "distance": "Distância",
        "project_code": "Código do projeto:",
        "work_order": "Ordem de serviço:",
        "contract_number": "Número do contrato:",
        "quality_check": "Verificação de qualidade:",
        "safety_compliance": "Conformidade de segurança:",
        "equipment_type": "Tipo de equipamento:",
        "serial_number": "Número de série:",
        "project_site": "Local do projeto:",
        "bill_to": "Faturar para:",
        "phone": "Telefone:",
        "email": "E-mail:",
        "item_code": "Código do item",
        "po_line_reference": "Linha PO",
        "work_completed_per_sow": "Trabalho concluído conforme SOW {sow_reference}",
        "project_manager": "Gerente de Projeto",
        "passed": "Aprovado",
        "verified": "Verificado"
    },
    "pl": {
        "invoice": "Faktura",
        "invoice_number": "Numer faktury",
        "invoice_date": "Data faktury",
        "due_date": "Termin płatności",
        "vendor": "Dostawca",
        "total_amount": "Kwota całkowita",
        "line_items": "Pozycje",
        "description": "Opis",
        "quantity": "Ilość",
        "unit_price": "Cena jednostkowa",
        "total": "Razem",
        "retention": "Zastrzeżenie",
        "retention_percentage": "Procent zastrzeżenia",
        "retention_applied": "Zastrzeżenie zastosowane",
        "liquidated_damages": "Kara umowna",
        "ld_applicable": "KU Zastosowalne",
        "ld_amount": "Kwota KU",
        "ld_applied": "KU Zastosowane",
        "evidence_references": "Dokumenty wspierające",
        "po_reference": "Numer PO",
        "sow_reference": "Numer SOW",
        "project_reference": "Numer projektu",
        "wbs_reference": "Numer WBS",
        "subtotal": "Suma częściowa",
        "tax": "Podatek",
        "payment_terms": "Warunki płatności",
        "payment_terms_text": "Warunki płatności: Netto 30",
        "questions": "Pytania?",
        "contact_us": "Skontaktuj się z nami pod adresem accounts@vendor.com lub (713) 555-0100",
        "thank_you": "Dziękujemy za współpracę!",
        "note_process_payment": "Uwaga: Prosimy o przetworzenie płatności w terminie. Skontaktuj się z nami w przypadku pytań.",
        "service_item": "Pozycja usługowa",
        "timesheet": "Karta czasu pracy",
        "completion_certificate": "Świadectwo ukończenia",
        "grn": "Dokument przyjęcia towaru",
        "grn_number": "Numer GRN:",
        "grn_date": "Data GRN:",
        "delivery_date": "Data dostawy:",
        "material_code": "Kod materiału:",
        "material_description": "Opis materiału:",
        "unit_of_measure": "Jednostka miary:",
        "received_quantity": "Otrzymana ilość:",
        "received_by": "Otrzymane przez:",
        "receipt_confirmed": "Przyjęcie potwierdzone",
        "worker_name": "Imię pracownika:",
        "employee_id": "ID pracownika:",
        "coverage_period": "Okres objęcia:",
        "total_hours_worked": "Łączne godziny pracy:",
        "invoice_reference": "Referencja faktury:",
        "project": "Projekt:",
        "date": "Data",
        "start": "Start",
        "end": "Koniec",
        "hours": "Godziny",
        "task": "Zadanie",
        "location": "Lokalizacja",
        "task_description": "Opis zadania",
        "time": "Czas",
        "activity": "Aktywność",
        "status": "Status",
        "operator": "Operator",
        "operator_signature": "Podpis operatora:",
        "worker_signature": "Podpis pracownika:",
        "supervisor_approval": "Zatwierdzenie przełożonego:",
        "approved_by": "Zatwierdzone przez:",
        "work_description": "Opis pracy:",
        "completion_date": "Data ukończenia:",
        "vessel_name": "Nazwa statku:",
        "log_date": "Data dziennika:",
        "hours_operated": "Godziny pracy:",
        "equipment_id": "ID sprzętu:",
        "hours_used": "Użyte godziny:",
        "certify_intro": "Niniejszym potwierdza się, że",
        "certify_completion": "zostało ukończone zgodnie z wymaganiami umowy.",
        "title": "Tytuł:",
        "signature": "Podpis:",
        "captain_signature": "Podpis kapitana:",
        "imo_number": "Numer IMO:",
        "flag_state": "Bandera:",
        "distance": "Odległość",
        "project_code": "Kod projektu:",
        "work_order": "Zlecenie pracy:",
        "contract_number": "Numer umowy:",
        "quality_check": "Kontrola jakości:",
        "safety_compliance": "Zgodność z bezpieczeństwem:",
        "equipment_type": "Typ sprzętu:",
        "serial_number": "Numer seryjny:",
        "project_site": "Miejsce projektu:",
        "bill_to": "Rachunek dla:",
        "phone": "Telefon:",
        "email": "E-mail:",
        "item_code": "Kod pozycji",
        "po_line_reference": "Linia PO",
        "work_completed_per_sow": "Praca ukończona zgodnie z SOW {sow_reference}",
        "project_manager": "Kierownik Projektu",
        "passed": "Zaliczony",
        "verified": "Zweryfikowany"
    },
    "hu": {
        "invoice": "Számla",
        "invoice_number": "Számlaszám",
        "invoice_date": "Számla dátuma",
        "due_date": "Fizetési határidő",
        "vendor": "Beszállító",
        "total_amount": "Összeg",
        "line_items": "Tételek",
        "description": "Leírás",
        "quantity": "Mennyiség",
        "unit_price": "Egységár",
        "total": "Összesen",
        "retention": "Visszatartás",
        "retention_percentage": "Visszatartási százalék",
        "retention_applied": "Visszatartás alkalmazva",
        "liquidated_damages": "Kártérítés",
        "ld_applicable": "KT Alkalmazandó",
        "ld_amount": "KT Összeg",
        "ld_applied": "KT Alkalmazva",
        "evidence_references": "Támogató dokumentumok",
        "po_reference": "PO Hivatkozás",
        "sow_reference": "SOW Hivatkozás",
        "project_reference": "Projekt hivatkozás",
        "wbs_reference": "WBS Hivatkozás",
        "subtotal": "Részösszeg",
        "tax": "Adó",
        "payment_terms": "Fizetési feltételek",
        "payment_terms_text": "Fizetési feltételek: Nettó 30",
        "questions": "Kérdések?",
        "contact_us": "Lépjen kapcsolatba velünk: accounts@vendor.com vagy (713) 555-0100",
        "thank_you": "Köszönjük az üzletet!",
        "note_process_payment": "Megjegyzés: Kérjük, feldolgozza a fizetést a feltételek szerint. Lépjen kapcsolatba velünk kérdésekkel.",
        "service_item": "Szolgáltatási tétel",
        "timesheet": "Időnyilvántartás",
        "completion_certificate": "Befejezési igazolás",
        "grn": "Áruátvételi igazolás",
        "grn_number": "GRN szám:",
        "grn_date": "GRN dátum:",
        "delivery_date": "Szállítási dátum:",
        "material_code": "Anyagkód:",
        "material_description": "Anyag leírása:",
        "unit_of_measure": "Mértékegység:",
        "received_quantity": "Átvett mennyiség:",
        "received_by": "Átvette:",
        "receipt_confirmed": "Átvétel megerősítve",
        "worker_name": "Munkavállaló neve:",
        "employee_id": "Alkalmazotti azonosító:",
        "coverage_period": "Fedezeti időszak:",
        "total_hours_worked": "Összes ledolgozott óra:",
        "invoice_reference": "Számla hivatkozás:",
        "project": "Projekt:",
        "date": "Dátum",
        "start": "Kezdés",
        "end": "Vég",
        "hours": "Óra",
        "task": "Feladat",
        "location": "Helyszín",
        "task_description": "Feladat leírása",
        "time": "Idő",
        "activity": "Tevékenység",
        "status": "Állapot",
        "operator": "Kezelő",
        "operator_signature": "Kezelő aláírása:",
        "worker_signature": "Dolgozó aláírása:",
        "supervisor_approval": "Felügyelő jóváhagyása:",
        "approved_by": "Jóváhagyta:",
        "work_description": "Munka leírása:",
        "completion_date": "Befejezés dátuma:",
        "vessel_name": "Hajó neve:",
        "log_date": "Napló dátuma:",
        "hours_operated": "Működési órák:",
        "equipment_id": "Berendezés azonosító:",
        "hours_used": "Felhasznált órák:",
        "certify_intro": "Ezennel igazoljuk, hogy",
        "certify_completion": "a szerződéses követelményeknek megfelelően befejeződött.",
        "title": "Cím:",
        "signature": "Aláírás:",
        "captain_signature": "Kapitány aláírása:",
        "imo_number": "IMO szám:",
        "flag_state": "Zászló állam:",
        "distance": "Távolság",
        "project_code": "Projekt kód:",
        "work_order": "Munkamegrendelés:",
        "contract_number": "Szerződésszám:",
        "quality_check": "Minőségellenőrzés:",
        "safety_compliance": "Biztonsági megfelelőség:",
        "equipment_type": "Berendezés típusa:",
        "serial_number": "Sorozatszám:",
        "project_site": "Projekt helyszín:",
        "bill_to": "Számlázás:",
        "phone": "Telefon:",
        "email": "E-mail:",
        "item_code": "Tételkód",
        "po_line_reference": "PO Sor",
        "work_completed_per_sow": "Munka befejezve SOW {sow_reference} szerint",
        "project_manager": "Projektmenedzser",
        "passed": "Sikeres",
        "verified": "Ellenőrizve"
    },
    "ro": {
        "invoice": "Factură",
        "invoice_number": "Număr factură",
        "invoice_date": "Data facturii",
        "due_date": "Data scadenței",
        "vendor": "Furnizor",
        "total_amount": "Suma totală",
        "line_items": "Articole",
        "description": "Descriere",
        "quantity": "Cantitate",
        "unit_price": "Preț unitar",
        "total": "Total",
        "retention": "Reținere",
        "retention_percentage": "Procent reținere",
        "retention_applied": "Reținere aplicată",
        "liquidated_damages": "Daune și interese",
        "ld_applicable": "DI Aplicabile",
        "ld_amount": "Suma DI",
        "ld_applied": "DI Aplicat",
        "evidence_references": "Documente justificative",
        "po_reference": "Referință PO",
        "sow_reference": "Referință SOW",
        "project_reference": "Referință proiect",
        "wbs_reference": "Referință WBS",
        "subtotal": "Subtotal",
        "tax": "Taxă",
        "payment_terms": "Termeni de plată",
        "payment_terms_text": "Termeni de plată: Net 30",
        "questions": "Întrebări?",
        "contact_us": "Contactați-ne la accounts@vendor.com sau (713) 555-0100",
        "thank_you": "Vă mulțumim pentru afacere!",
        "note_process_payment": "Notă: Vă rugăm să procesați plata în termenii stabiliți. Contactați-ne pentru întrebări.",
        "service_item": "Articol de serviciu",
        "timesheet": "Fișă de pontaj",
        "completion_certificate": "Certificat de finalizare",
        "grn": "Notă de primire mărfuri",
        "grn_number": "Număr GRN:",
        "grn_date": "Data GRN:",
        "delivery_date": "Data livrării:",
        "material_code": "Cod material:",
        "material_description": "Descriere material:",
        "unit_of_measure": "Unitate de măsură:",
        "received_quantity": "Cantitate primită:",
        "received_by": "Primit de:",
        "receipt_confirmed": "Primire confirmată",
        "worker_name": "Nume lucrător:",
        "employee_id": "ID angajat:",
        "coverage_period": "Perioada de acoperire:",
        "total_hours_worked": "Total ore lucrate:",
        "invoice_reference": "Referință factură:",
        "project": "Proiect:",
        "date": "Dată",
        "start": "Început",
        "end": "Sfârșit",
        "hours": "Ore",
        "task": "Sarcină",
        "location": "Locație",
        "task_description": "Descriere sarcină",
        "time": "Ora",
        "activity": "Activitate",
        "status": "Status",
        "operator": "Operator",
        "operator_signature": "Semnătură operator:",
        "worker_signature": "Semnătură lucrător:",
        "supervisor_approval": "Aprobare supervizor:",
        "approved_by": "Aprobat de:",
        "work_description": "Descriere lucrare:",
        "completion_date": "Data finalizării:",
        "vessel_name": "Nume navă:",
        "log_date": "Data jurnal:",
        "hours_operated": "Ore de funcționare:",
        "equipment_id": "ID echipament:",
        "hours_used": "Ore utilizate:",
        "certify_intro": "Se certifică că",
        "certify_completion": "a fost finalizat în conformitate cu cerințele contractului.",
        "title": "Titlu:",
        "signature": "Semnătură:",
        "captain_signature": "Semnătură căpitan:",
        "imo_number": "Număr IMO:",
        "flag_state": "Pavilion:",
        "distance": "Distanță",
        "project_code": "Cod proiect:",
        "work_order": "Comandă de lucru:",
        "contract_number": "Număr contract:",
        "quality_check": "Verificare calitate:",
        "safety_compliance": "Conformitate siguranță:",
        "equipment_type": "Tip echipament:",
        "serial_number": "Număr de serie:",
        "project_site": "Locație proiect:",
        "bill_to": "Facturare către:",
        "phone": "Telefon:",
        "email": "E-mail:",
        "item_code": "Cod articol",
        "po_line_reference": "Linie PO",
        "work_completed_per_sow": "Lucrare finalizată conform SOW {sow_reference}",
        "project_manager": "Manager de Proiect",
        "passed": "Trecut",
        "verified": "Verificat"
    },
    "bg": {
        "invoice": "Фактура",
        "invoice_number": "Номер на фактура",
        "invoice_date": "Дата на фактура",
        "due_date": "Срок за плащане",
        "vendor": "Доставчик",
        "total_amount": "Обща сума",
        "line_items": "Артикули",
        "description": "Описание",
        "quantity": "Количество",
        "unit_price": "Единична цена",
        "total": "Общо",
        "retention": "Удържане",
        "retention_percentage": "Процент удържане",
        "retention_applied": "Удържане приложено",
        "liquidated_damages": "Обезщетение",
        "ld_applicable": "ОБ Приложимо",
        "ld_amount": "Сума ОБ",
        "ld_applied": "ОБ Приложено",
        "evidence_references": "Поддържащи документи",
        "po_reference": "Референция PO",
        "sow_reference": "Референция SOW",
        "project_reference": "Референция проект",
        "wbs_reference": "Референция WBS",
        "subtotal": "Междинна сума",
        "tax": "Данък",
        "payment_terms": "Условия за плащане",
        "payment_terms_text": "Условия за плащане: Нето 30",
        "questions": "Въпроси?",
        "contact_us": "Свържете се с нас на accounts@vendor.com или (713) 555-0100",
        "thank_you": "Благодарим за бизнеса!",
        "note_process_payment": "Забележка: Моля, обработете плащането в сроковете. Свържете се с нас за въпроси.",
        "service_item": "Сервизна позиция",
        "timesheet": "Табел",
        "completion_certificate": "Сертификат за завършване",
        "grn": "Нота за получаване на стоки",
        "grn_number": "Номер GRN:",
        "grn_date": "Дата GRN:",
        "delivery_date": "Дата на доставка:",
        "material_code": "Код на материал:",
        "material_description": "Описание на материал:",
        "unit_of_measure": "Мерна единица:",
        "received_quantity": "Получено количество:",
        "received_by": "Получено от:",
        "receipt_confirmed": "Получаване потвърдено",
        "worker_name": "Име на работник:",
        "employee_id": "ID на служител:",
        "coverage_period": "Период на покритие:",
        "total_hours_worked": "Общо отработени часове:",
        "invoice_reference": "Референция на фактура:",
        "project": "Проект:",
        "date": "Дата",
        "start": "Начало",
        "end": "Край",
        "hours": "Часове",
        "task": "Задача",
        "location": "Местоположение",
        "task_description": "Описание на задача",
        "time": "Време",
        "activity": "Дейност",
        "status": "Статус",
        "operator": "Оператор",
        "operator_signature": "Подпис на оператор:",
        "worker_signature": "Подпис на работник:",
        "supervisor_approval": "Одобрение на ръководител:",
        "approved_by": "Одобрено от:",
        "work_description": "Описание на работа:",
        "completion_date": "Дата на завършване:",
        "vessel_name": "Име на кораб:",
        "log_date": "Дата на дневник:",
        "hours_operated": "Работни часове:",
        "equipment_id": "ID на оборудване:",
        "hours_used": "Използвани часове:",
        "certify_intro": "Настоящето удостоверява, че",
        "certify_completion": "е завършено в съответствие с изискванията на договора.",
        "title": "Заглавие:",
        "signature": "Подпис:",
        "captain_signature": "Подпис на капитан:",
        "imo_number": "IMO номер:",
        "flag_state": "Флаг:",
        "distance": "Разстояние",
        "project_code": "Код на проект:",
        "work_order": "Работна поръчка:",
        "contract_number": "Номер на договор:",
        "quality_check": "Проверка на качеството:",
        "safety_compliance": "Съответствие със сигурността:",
        "equipment_type": "Тип оборудване:",
        "serial_number": "Сериен номер:",
        "project_site": "Място на проект:",
        "bill_to": "Фактура до:",
        "phone": "Телефон:",
        "email": "Имейл:",
        "item_code": "Код на артикул",
        "po_line_reference": "PO Линия",
        "work_completed_per_sow": "Работа завършена според SOW {sow_reference}",
        "project_manager": "Мениджър на проект",
        "passed": "Преминат",
        "verified": "Проверен"
    },
    "sv": {
        "invoice": "Faktura",
        "invoice_number": "Fakturanummer",
        "invoice_date": "Fakturadatum",
        "due_date": "Förfallodatum",
        "vendor": "Leverantör",
        "total_amount": "Totalt belopp",
        "line_items": "Rader",
        "description": "Beskrivning",
        "quantity": "Kvantitet",
        "unit_price": "Styckpris",
        "total": "Totalt",
        "retention": "Kvarhållning",
        "retention_percentage": "Kvarhållningsprocent",
        "retention_applied": "Kvarhållning tillämpad",
        "liquidated_damages": "Konventionalstraff",
        "ld_applicable": "KS Tillämpligt",
        "ld_amount": "KS Belopp",
        "ld_applied": "KS Tillämpat",
        "evidence_references": "Stöddokument",
        "po_reference": "PO-referens",
        "sow_reference": "SOW-referens",
        "project_reference": "Projektreferens",
        "wbs_reference": "WBS-referens",
        "subtotal": "Delsumma",
        "tax": "Skatt",
        "payment_terms": "Betalningsvillkor",
        "payment_terms_text": "Betalningsvillkor: Netto 30",
        "questions": "Frågor?",
        "contact_us": "Kontakta oss på accounts@vendor.com eller (713) 555-0100",
        "thank_you": "Tack för ditt företag!",
        "note_process_payment": "Notera: Vänligen behandla betalningen inom villkoren. Kontakta oss för frågor.",
        "service_item": "Serviceartikel",
        "timesheet": "Tidrapport",
        "completion_certificate": "Slutförandebetyg",
        "grn": "Mottagningsnota",
        "grn_number": "GRN-nummer:",
        "grn_date": "GRN-datum:",
        "delivery_date": "Leveransdatum:",
        "material_code": "Materialkod:",
        "material_description": "Materialbeskrivning:",
        "unit_of_measure": "Mätenhet:",
        "received_quantity": "Mottagen kvantitet:",
        "received_by": "Mottagen av:",
        "receipt_confirmed": "Mottagande bekräftat",
        "worker_name": "Arbetarnamn:",
        "employee_id": "Anställnings-ID:",
        "coverage_period": "Täckningsperiod:",
        "total_hours_worked": "Totalt arbetade timmar:",
        "invoice_reference": "Fakturareferens:",
        "project": "Projekt:",
        "date": "Datum",
        "start": "Start",
        "end": "Slut",
        "hours": "Timmar",
        "task": "Uppgift",
        "location": "Plats",
        "task_description": "Uppgiftsbeskrivning",
        "time": "Tid",
        "activity": "Aktivitet",
        "status": "Status",
        "operator": "Operatör",
        "operator_signature": "Operatörsignatur:",
        "worker_signature": "Arbetssignatur:",
        "supervisor_approval": "Handledargodkännande:",
        "approved_by": "Godkänd av:",
        "work_description": "Arbetsbeskrivning:",
        "completion_date": "Slutförandedatum:",
        "vessel_name": "Fartygsnamn:",
        "log_date": "Loggdatum:",
        "hours_operated": "Driftstimmar:",
        "equipment_id": "Utrustnings-ID:",
        "hours_used": "Använda timmar:",
        "certify_intro": "Detta intygar att",
        "certify_completion": "har slutförts i enlighet med kontraktskraven.",
        "title": "Titel:",
        "signature": "Signatur:",
        "captain_signature": "Kaptens signatur:",
        "imo_number": "IMO-nummer:",
        "flag_state": "Flagga:",
        "distance": "Avstånd",
        "project_code": "Projektkod:",
        "work_order": "Arbetsorder:",
        "contract_number": "Kontraktsnummer:",
        "quality_check": "Kvalitetskontroll:",
        "safety_compliance": "Säkerhetsöverensstämmelse:",
        "equipment_type": "Utrustningstyp:",
        "serial_number": "Serienummer:",
        "project_site": "Projektplats:",
        "bill_to": "Fakturera till:",
        "phone": "Telefon:",
        "email": "E-post:",
        "item_code": "Artikelkod",
        "po_line_reference": "PO Rad",
        "work_completed_per_sow": "Arbete slutfört enligt SOW {sow_reference}",
        "project_manager": "Projektledare",
        "passed": "Godkänd",
        "verified": "Verifierad"
    },
    "tr": {
        "invoice": "Fatura",
        "invoice_number": "Fatura Numarası",
        "invoice_date": "Fatura Tarihi",
        "due_date": "Vade Tarihi",
        "vendor": "Tedarikçi",
        "total_amount": "Toplam Tutar",
        "line_items": "Kalemler",
        "description": "Açıklama",
        "quantity": "Miktar",
        "unit_price": "Birim Fiyat",
        "total": "Toplam",
        "retention": "Kesinti",
        "retention_percentage": "Kesinti Yüzdesi",
        "retention_applied": "Kesinti Uygulandı",
        "liquidated_damages": "Tazminat",
        "ld_applicable": "TZ Uygulanabilir",
        "ld_amount": "TZ Tutarı",
        "ld_applied": "TZ Uygulandı",
        "evidence_references": "Destekleyici Belgeler",
        "po_reference": "PO Referansı",
        "sow_reference": "SOW Referansı",
        "project_reference": "Proje Referansı",
        "wbs_reference": "WBS Referansı",
        "subtotal": "Ara Toplam",
        "tax": "Vergi",
        "payment_terms": "Ödeme Koşulları",
        "payment_terms_text": "Ödeme Koşulları: Net 30",
        "questions": "Sorular?",
        "contact_us": "Bize accounts@vendor.com veya (713) 555-0100 adresinden ulaşın",
        "thank_you": "İşiniz için teşekkürler!",
        "note_process_payment": "Not: Lütfen ödemeyi koşullar dahilinde işleyin. Sorular için bizimle iletişime geçin.",
        "service_item": "Hizmet Kalemi",
        "timesheet": "Zaman Çizelgesi",
        "completion_certificate": "Tamamlanma Sertifikası",
        "grn": "Mal Kabul Notu",
        "grn_number": "GRN Numarası:",
        "grn_date": "GRN Tarihi:",
        "delivery_date": "Teslimat Tarihi:",
        "material_code": "Malzeme Kodu:",
        "material_description": "Malzeme Açıklaması:",
        "unit_of_measure": "Ölçü Birimi:",
        "received_quantity": "Alınan Miktar:",
        "received_by": "Alan:",
        "receipt_confirmed": "Alım Onaylandı",
        "worker_name": "İşçi Adı:",
        "employee_id": "Çalışan ID:",
        "coverage_period": "Kapsam Dönemi:",
        "total_hours_worked": "Toplam Çalışılan Saat:",
        "invoice_reference": "Fatura Referansı:",
        "project": "Proje:",
        "date": "Tarih",
        "start": "Başlangıç",
        "end": "Bitiş",
        "hours": "Saat",
        "task": "Görev",
        "location": "Konum",
        "task_description": "Görev Açıklaması",
        "time": "Zaman",
        "activity": "Aktivite",
        "status": "Durum",
        "operator": "Operatör",
        "operator_signature": "Operatör İmzası:",
        "worker_signature": "İşçi İmzası:",
        "supervisor_approval": "Süpervizör Onayı:",
        "approved_by": "Onaylayan:",
        "work_description": "İş Açıklaması:",
        "completion_date": "Tamamlanma Tarihi:",
        "vessel_name": "Gemi Adı:",
        "log_date": "Günlük Tarihi:",
        "hours_operated": "Çalışma Saatleri:",
        "equipment_id": "Ekipman ID:",
        "hours_used": "Kullanılan Saatler:",
        "certify_intro": "Bu belge ile teyit edilir ki",
        "certify_completion": "sözleşme gereksinimlerine uygun olarak tamamlanmıştır.",
        "title": "Başlık:",
        "signature": "İmza:",
        "captain_signature": "Kaptan İmzası:",
        "imo_number": "IMO Numarası:",
        "flag_state": "Bayrak:",
        "distance": "Mesafe",
        "project_code": "Proje Kodu:",
        "work_order": "İş Emri:",
        "contract_number": "Sözleşme Numarası:",
        "quality_check": "Kalite Kontrolü:",
        "safety_compliance": "Güvenlik Uyumluluğu:",
        "equipment_type": "Ekipman Tipi:",
        "serial_number": "Seri Numarası:",
        "project_site": "Proje Alanı:",
        "bill_to": "Fatura Edilecek:",
        "phone": "Telefon:",
        "email": "E-posta:",
        "item_code": "Kalem Kodu",
        "po_line_reference": "PO Satırı",
        "work_completed_per_sow": "SOW {sow_reference} uyarınca tamamlanan iş",
        "project_manager": "Proje Yöneticisi",
        "passed": "Geçti",
        "verified": "Doğrulandı"
    },
    "zh": {
        "invoice": "发票",
        "invoice_number": "发票编号",
        "invoice_date": "发票日期",
        "due_date": "到期日期",
        "vendor": "供应商",
        "total_amount": "总金额",
        "line_items": "项目",
        "description": "描述",
        "quantity": "数量",
        "unit_price": "单价",
        "total": "总计",
        "retention": "保留金",
        "retention_percentage": "保留金百分比",
        "retention_applied": "已应用保留金",
        "liquidated_damages": "违约金",
        "ld_applicable": "违约金适用",
        "ld_amount": "违约金金额",
        "ld_applied": "已应用违约金",
        "evidence_references": "支持文件",
        "po_reference": "采购订单参考",
        "sow_reference": "工作说明书参考",
        "project_reference": "项目参考",
        "wbs_reference": "工作分解结构参考",
        "subtotal": "小计",
        "tax": "税费",
        "payment_terms": "付款条件",
        "payment_terms_text": "付款条件: 净30天",
        "questions": "有问题？",
        "contact_us": "通过 accounts@vendor.com 或 (713) 555-0100 联系我们",
        "thank_you": "感谢您的业务！",
        "note_process_payment": "注意：请在期限内处理付款。如有问题请联系我们。",
        "service_item": "服务项目",
        "timesheet": "时间表",
        "completion_certificate": "完工证书",
        "grn": "收货单",
        "grn_number": "GRN编号:",
        "grn_date": "GRN日期:",
        "delivery_date": "交货日期:",
        "material_code": "物料代码:",
        "material_description": "物料描述:",
        "unit_of_measure": "计量单位:",
        "received_quantity": "收货数量:",
        "received_by": "收货人:",
        "receipt_confirmed": "收货确认",
        "worker_name": "工人姓名:",
        "employee_id": "员工ID:",
        "coverage_period": "覆盖期间:",
        "total_hours_worked": "总工作小时:",
        "invoice_reference": "发票参考:",
        "project": "项目:",
        "date": "日期",
        "start": "开始",
        "end": "结束",
        "hours": "小时",
        "task": "任务",
        "location": "位置",
        "task_description": "任务描述",
        "time": "时间",
        "activity": "活动",
        "status": "状态",
        "operator": "操作员",
        "operator_signature": "操作员签名:",
        "worker_signature": "工人签名:",
        "supervisor_approval": "主管批准:",
        "approved_by": "批准人:",
        "work_description": "工作描述:",
        "completion_date": "完成日期:",
        "vessel_name": "船舶名称:",
        "log_date": "日志日期:",
        "hours_operated": "运行小时:",
        "equipment_id": "设备ID:",
        "hours_used": "使用小时:",
        "certify_intro": "兹证明",
        "certify_completion": "已按照合同要求完成。",
        "title": "职位:",
        "signature": "签名:",
        "captain_signature": "船长签名:",
        "imo_number": "IMO编号:",
        "flag_state": "船旗国:",
        "distance": "距离",
        "project_code": "项目代码:",
        "work_order": "工作单:",
        "contract_number": "合同编号:",
        "quality_check": "质量检查:",
        "safety_compliance": "安全合规:",
        "equipment_type": "设备类型:",
        "serial_number": "序列号:",
        "project_site": "项目地点:",
        "bill_to": "账单寄至:",
        "phone": "电话:",
        "email": "电子邮件:",
        "item_code": "项目代码",
        "po_line_reference": "PO行",
        "work_completed_per_sow": "根据SOW {sow_reference}完成的工作",
        "project_manager": "项目经理",
        "passed": "通过",
        "verified": "已验证"
    },
    "id": {
        "invoice": "Faktur",
        "invoice_number": "Nomor Faktur",
        "invoice_date": "Tanggal Faktur",
        "due_date": "Tanggal Jatuh Tempo",
        "vendor": "Pemasok",
        "total_amount": "Jumlah Total",
        "line_items": "Item",
        "description": "Deskripsi",
        "quantity": "Kuantitas",
        "unit_price": "Harga Satuan",
        "total": "Total",
        "retention": "Retensi",
        "retention_percentage": "Persentase Retensi",
        "retention_applied": "Retensi Diterapkan",
        "liquidated_damages": "Ganti Rugi",
        "ld_applicable": "GR Berlaku",
        "ld_amount": "Jumlah GR",
        "ld_applied": "GR Diterapkan",
        "evidence_references": "Dokumen Pendukung",
        "po_reference": "Referensi PO",
        "sow_reference": "Referensi SOW",
        "project_reference": "Referensi Proyek",
        "wbs_reference": "Referensi WBS",
        "subtotal": "Subtotal",
        "tax": "Pajak",
        "payment_terms": "Syarat Pembayaran",
        "payment_terms_text": "Syarat Pembayaran: Netto 30",
        "questions": "Pertanyaan?",
        "contact_us": "Hubungi kami di accounts@vendor.com atau (713) 555-0100",
        "thank_you": "Terima kasih atas bisnis Anda!",
        "note_process_payment": "Catatan: Harap proses pembayaran dalam syarat. Hubungi kami untuk pertanyaan.",
        "service_item": "Item Layanan",
        "timesheet": "Lembar Waktu",
        "completion_certificate": "Sertifikat Penyelesaian",
        "grn": "Nota Penerimaan Barang",
        "grn_number": "Nomor GRN:",
        "grn_date": "Tanggal GRN:",
        "delivery_date": "Tanggal pengiriman:",
        "material_code": "Kode material:",
        "material_description": "Deskripsi material:",
        "unit_of_measure": "Satuan ukur:",
        "received_quantity": "Jumlah diterima:",
        "received_by": "Diterima oleh:",
        "receipt_confirmed": "Penerimaan dikonfirmasi",
        "worker_name": "Nama Pekerja:",
        "employee_id": "ID Karyawan:",
        "coverage_period": "Periode Cakupan:",
        "total_hours_worked": "Total Jam Bekerja:",
        "invoice_reference": "Referensi Faktur:",
        "project": "Proyek:",
        "date": "Tanggal",
        "start": "Mulai",
        "end": "Selesai",
        "hours": "Jam",
        "task": "Tugas",
        "location": "Lokasi",
        "task_description": "Deskripsi Tugas",
        "time": "Waktu",
        "activity": "Aktivitas",
        "status": "Status",
        "operator": "Operator",
        "operator_signature": "Tanda Tangan Operator:",
        "worker_signature": "Tanda Tangan Pekerja:",
        "supervisor_approval": "Persetujuan Supervisor:",
        "approved_by": "Disetujui Oleh:",
        "work_description": "Deskripsi Pekerjaan:",
        "completion_date": "Tanggal Penyelesaian:",
        "vessel_name": "Nama Kapal:",
        "log_date": "Tanggal Log:",
        "hours_operated": "Jam Operasi:",
        "equipment_id": "ID Peralatan:",
        "hours_used": "Jam Digunakan:",
        "certify_intro": "Dengan ini menyatakan bahwa",
        "certify_completion": "telah diselesaikan sesuai dengan persyaratan kontrak.",
        "title": "Judul:",
        "signature": "Tanda Tangan:",
        "captain_signature": "Tanda Tangan Kapten:",
        "imo_number": "Nomor IMO:",
        "flag_state": "Bendera:",
        "distance": "Jarak",
        "project_code": "Kode Proyek:",
        "work_order": "Perintah Kerja:",
        "contract_number": "Nomor Kontrak:",
        "quality_check": "Pemeriksaan Kualitas:",
        "safety_compliance": "Kepatuhan Keselamatan:",
        "equipment_type": "Jenis Peralatan:",
        "serial_number": "Nomor Seri:",
        "project_site": "Lokasi Proyek:",
        "bill_to": "Tagih ke:",
        "phone": "Telepon:",
        "email": "Email:",
        "item_code": "Kode Item",
        "po_line_reference": "Baris PO",
        "work_completed_per_sow": "Pekerjaan selesai sesuai SOW {sow_reference}",
        "project_manager": "Manajer Proyek",
        "passed": "Lulus",
        "verified": "Terverifikasi"
    },
    "ms": {
        "invoice": "Invois",
        "invoice_number": "Nombor Invois",
        "invoice_date": "Tarikh Invois",
        "due_date": "Tarikh Tamat Tempoh",
        "vendor": "Pembekal",
        "total_amount": "Jumlah Keseluruhan",
        "line_items": "Item",
        "description": "Penerangan",
        "quantity": "Kuantiti",
        "unit_price": "Harga Unit",
        "total": "Jumlah",
        "retention": "Penahanan",
        "retention_percentage": "Peratusan Penahanan",
        "retention_applied": "Penahanan Digunakan",
        "liquidated_damages": "Ganti Rugi",
        "ld_applicable": "GR Berkenaan",
        "ld_amount": "Jumlah GR",
        "ld_applied": "GR Digunakan",
        "evidence_references": "Dokumen Sokongan",
        "po_reference": "Rujukan PO",
        "sow_reference": "Rujukan SOW",
        "project_reference": "Rujukan Projek",
        "wbs_reference": "Rujukan WBS",
        "subtotal": "Jumlah kecil",
        "tax": "Cukai",
        "payment_terms": "Terma Pembayaran",
        "payment_terms_text": "Terma Pembayaran: Bersih 30",
        "questions": "Soalan?",
        "contact_us": "Hubungi kami di accounts@vendor.com atau (713) 555-0100",
        "thank_you": "Terima kasih atas perniagaan anda!",
        "note_process_payment": "Nota: Sila proses pembayaran dalam terma. Hubungi kami untuk soalan.",
        "service_item": "Item Perkhidmatan",
        "timesheet": "Lembaran Masa",
        "completion_certificate": "Sijil Penyiapan",
        "grn": "Nota Penerimaan Barang",
        "grn_number": "Nombor GRN:",
        "grn_date": "Tarikh GRN:",
        "delivery_date": "Tarikh penghantaran:",
        "material_code": "Kod bahan:",
        "material_description": "Penerangan bahan:",
        "unit_of_measure": "Unit ukuran:",
        "received_quantity": "Kuantiti diterima:",
        "received_by": "Diterima oleh:",
        "receipt_confirmed": "Penerimaan disahkan",
        "worker_name": "Nama Pekerja:",
        "employee_id": "ID Pekerja:",
        "coverage_period": "Tempoh Perlindungan:",
        "total_hours_worked": "Jumlah Jam Bekerja:",
        "invoice_reference": "Rujukan Invois:",
        "project": "Projek:",
        "date": "Tarikh",
        "start": "Mula",
        "end": "Tamat",
        "hours": "Jam",
        "task": "Tugas",
        "location": "Lokasi",
        "task_description": "Penerangan Tugas",
        "time": "Masa",
        "activity": "Aktiviti",
        "status": "Status",
        "operator": "Pengendali",
        "operator_signature": "Tandatangan Pengendali:",
        "worker_signature": "Tandatangan Pekerja:",
        "supervisor_approval": "Kelulusan Penyelia:",
        "approved_by": "Diluluskan Oleh:",
        "work_description": "Penerangan Kerja:",
        "completion_date": "Tarikh Penyiapan:",
        "vessel_name": "Nama Kapal:",
        "log_date": "Tarikh Log:",
        "hours_operated": "Jam Operasi:",
        "equipment_id": "ID Peralatan:",
        "hours_used": "Jam Digunakan:",
        "certify_intro": "Dengan ini mengesahkan bahawa",
        "certify_completion": "telah disiapkan mengikut keperluan kontrak.",
        "title": "Tajuk:",
        "signature": "Tandatangan:",
        "captain_signature": "Tandatangan Kapten:",
        "imo_number": "Nombor IMO:",
        "flag_state": "Bendera:",
        "distance": "Jarak",
        "project_code": "Kod Projek:",
        "work_order": "Perintah Kerja:",
        "contract_number": "Nombor Kontrak:",
        "quality_check": "Pemeriksaan Kualiti:",
        "safety_compliance": "Pematuhan Keselamatan:",
        "equipment_type": "Jenis Peralatan:",
        "serial_number": "Nombor Siri:",
        "project_site": "Lokasi Projek:",
        "bill_to": "Bil kepada:",
        "phone": "Telefon:",
        "email": "E-mel:",
        "item_code": "Kod Item",
        "po_line_reference": "Baris PO",
        "work_completed_per_sow": "Kerja siap mengikut SOW {sow_reference}",
        "project_manager": "Pengurus Projek",
        "passed": "Lulus",
        "verified": "Disahkan"
    }
}


def assign_language_to_invoice(non_english_pct: float = 0.60) -> str:
    """Assign language to invoice based on non-English percentage.
    
    Args:
        non_english_pct: Percentage of invoices that should be non-English (0.0-1.0, default: 0.60 = 60%)
    
    Returns:
        ISO 639-1 language code (e.g., 'en', 'de', 'fr')
    """
    english_pct = 1.0 - non_english_pct
    if random.random() < english_pct:
        return "en"
    else:
        # Equal probability for all non-English languages
        return random.choice(NON_ENGLISH_LANGUAGES)


def get_language_template(language: str) -> Dict[str, str]:
    """Get language template for specified language.
    
    Args:
        language: ISO 639-1 language code
        
    Returns:
        Dictionary of translated terms
    """
    return LANGUAGE_TEMPLATES.get(language, LANGUAGE_TEMPLATES["en"])


# Global variable to track registered CJK font
_REGISTERED_CJK_FONT = None


def register_cjk_fonts() -> Optional[str]:
    """Register CJK (Chinese, Japanese, Korean) fonts for ReportLab if available.
    
    Tries to register fonts in this order:
    1. System fonts (common locations on macOS, Linux, Windows)
    2. UnicodeCIDFont with common Chinese font names
    3. Custom font path from environment variable CJK_FONT_PATH (if set)
    
    To use a custom font, set the environment variable:
        export CJK_FONT_PATH="/path/to/your/chinese-font.ttf"
    
    Returns:
        Registered font name if successful, None otherwise
    """
    if not REPORTLAB_AVAILABLE:
        return None
    
    # Check for custom font path from environment variable first
    custom_font_path = os.environ.get("CJK_FONT_PATH")
    if custom_font_path and os.path.exists(custom_font_path):
        try:
            font_name = "CJKFont"
            pdfmetrics.registerFont(TTFont(font_name, custom_font_path))
            return font_name
        except Exception as e:
            print(f"Warning: Failed to register custom CJK font from {custom_font_path}: {e}")
    
    # Common font paths to check
    import platform
    system = platform.system()
    
    font_paths = []
    if system == "Darwin":  # macOS
        font_paths = [
            "/System/Library/Fonts/STHeiti Light.ttc",  # Heiti SC (Simplified Chinese)
            "/System/Library/Fonts/STHeiti Medium.ttc",  # Heiti TC (Traditional Chinese)
            "/System/Library/Fonts/Supplemental/Songti.ttc",  # Songti (Song font)
            "/Library/Fonts/Arial Unicode.ttf",  # Arial Unicode (if installed)
            # PingFang is usually in a different location, check common paths
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Supplemental/PingFang.ttc",
        ]
    elif system == "Linux":
        font_paths = [
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/arphic/uming.ttc",
        ]
    elif system == "Windows":
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",  # Microsoft YaHei
            "C:/Windows/Fonts/simsun.ttc",  # SimSun
            "C:/Windows/Fonts/simhei.ttf",  # SimHei
        ]
    
    # Try to register a TTF/TTC font from system paths
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font_name = "CJKFont"
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                return font_name
            except Exception:
                continue
    
    # Try UnicodeCIDFont with common Chinese font names
    # These are built-in font names that ReportLab might support
    cid_font_names = [
        "STSong-Light",  # Song Ti (common Chinese font)
        "STSongStd-Light",
        "HeiseiMin-W3",  # Japanese, but might work for some Chinese
    ]
    
    for font_name in cid_font_names:
        try:
            pdfmetrics.registerFont(UnicodeCIDFont(font_name))
            return font_name
        except Exception:
            continue
    
    return None


def get_font_for_language(language: str) -> str:
    """Get appropriate font name for language.
    
    Args:
        language: ISO 639-1 language code
        
    Returns:
        Font name to use (defaults to 'Helvetica' if special fonts not available)
    """
    global _REGISTERED_CJK_FONT
    
    # For Chinese/Mandarin, try to use registered CJK font
    if language == "zh":
        if _REGISTERED_CJK_FONT is None:
            # Try to register CJK fonts on first use
            _REGISTERED_CJK_FONT = register_cjk_fonts()
        
        if _REGISTERED_CJK_FONT:
            return _REGISTERED_CJK_FONT
        else:
            # Fallback: Helvetica doesn't support CJK, will show squares
            # Try to use a Unicode font that might support more characters
            # Note: User should install a CJK font (e.g., Noto Sans CJK) for proper rendering
            # The font will be auto-detected if available in system paths
            print(f"  ⚠ Warning: CJK font not found for language '{language}'. Some characters may display as squares.")
            print(f"     To fix: Install a CJK font (e.g., Noto Sans CJK) or set CJK_FONT_PATH environment variable")
            return "Helvetica"
    
    # For all other languages, use Helvetica (supports most European languages)
    return "Helvetica"


def create_database_schema(db_path: str) -> None:
    """Create all database tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # ============================================================================
    # ERP System Tables
    # ============================================================================
    
    # Vendors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            vendor_id TEXT PRIMARY KEY,
            vendor_name TEXT NOT NULL,
            vendor_code TEXT UNIQUE NOT NULL,
            tax_id TEXT,
            payment_terms TEXT,
            currency TEXT DEFAULT 'GBP',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Purchase Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            po_number TEXT PRIMARY KEY,
            vendor_id TEXT NOT NULL,
            sow_id TEXT,
            po_date DATE NOT NULL,
            status TEXT NOT NULL,
            total_amount DECIMAL(10, 2) NOT NULL,
            currency TEXT DEFAULT 'GBP',
            project_id TEXT,
            approver TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
            FOREIGN KEY (sow_id) REFERENCES statements_of_work(sow_id)
        )
    """)
    
    # PO Line Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS po_line_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT NOT NULL,
            line_number INTEGER,
            item_code TEXT,
            description TEXT NOT NULL,
            quantity DECIMAL(10, 2) NOT NULL,
            unit_price DECIMAL(10, 2) NOT NULL,
            total DECIMAL(10, 2) NOT NULL,
            rate_card_id TEXT,
            wbs_id TEXT,
            role TEXT,
            rate DECIMAL(10, 2),
            material_category TEXT,
            FOREIGN KEY (po_number) REFERENCES purchase_orders(po_number) ON DELETE CASCADE,
            FOREIGN KEY (wbs_id) REFERENCES work_breakdown_structure(wbs_id)
        )
    """)
    
    # Payment History table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_history (
            payment_id TEXT PRIMARY KEY,
            invoice_id TEXT,
            po_number TEXT,
            vendor_id TEXT NOT NULL,
            payment_date DATE,
            payment_amount DECIMAL(10, 2),
            payment_status TEXT,
            payment_method TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
        )
    """)
    
    # ============================================================================
    # Contract Management Tables
    # ============================================================================
    
    # Statements of Work table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS statements_of_work (
            sow_id TEXT PRIMARY KEY,
            sow_number TEXT UNIQUE NOT NULL,
            vendor_id TEXT,
            project_id TEXT,
            invoice_type TEXT,
            pricing_model TEXT,
            retention_percentage DECIMAL(5, 2),
            retention_held DECIMAL(10, 2),
            ld_applicable BOOLEAN,
            ld_rate_per_day DECIMAL(10, 2),
            start_date DATE,
            end_date DATE,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
        )
    """)
    
    # Rate Cards table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rate_cards (
            rate_card_id TEXT PRIMARY KEY,
            vendor_id TEXT,
            sow_id TEXT,
            item_code TEXT,
            description TEXT,
            unit_price DECIMAL(10, 2),
            unit_of_measure TEXT,
            effective_date DATE,
            expiry_date DATE,
            status TEXT,
            FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
            FOREIGN KEY (sow_id) REFERENCES statements_of_work(sow_id)
        )
    """)
    
    # Commercial Terms table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commercial_terms (
            term_id TEXT PRIMARY KEY,
            sow_id TEXT,
            term_type TEXT,
            term_value TEXT,
            applicable_from DATE,
            applicable_to DATE,
            FOREIGN KEY (sow_id) REFERENCES statements_of_work(sow_id)
        )
    """)
    
    # ============================================================================
    # Project / Asset Tracking Tables
    # ============================================================================
    
    # Projects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY,
            project_code TEXT UNIQUE NOT NULL,
            project_name TEXT NOT NULL,
            project_type TEXT,
            status TEXT,
            start_date DATE,
            end_date DATE,
            budget DECIMAL(12, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Work Breakdown Structure table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_breakdown_structure (
            wbs_id TEXT PRIMARY KEY,
            wbs_code TEXT UNIQUE NOT NULL,
            project_id TEXT NOT NULL,
            parent_wbs_id TEXT,
            wbs_name TEXT NOT NULL,
            wbs_level INTEGER,
            budget_allocation DECIMAL(12, 2),
            status TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(project_id),
            FOREIGN KEY (parent_wbs_id) REFERENCES work_breakdown_structure(wbs_id)
        )
    """)
    
    # Milestones table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS milestones (
            milestone_id TEXT PRIMARY KEY,
            milestone_code TEXT,
            project_id TEXT,
            wbs_id TEXT,
            sow_id TEXT,
            milestone_name TEXT,
            milestone_type TEXT,
            planned_date DATE,
            actual_date DATE,
            milestone_cap_amount DECIMAL(10, 2),
            approval_status TEXT,
            approved_by TEXT,
            approved_date DATE,
            FOREIGN KEY (project_id) REFERENCES projects(project_id),
            FOREIGN KEY (sow_id) REFERENCES statements_of_work(sow_id)
        )
    """)
    
    # ============================================================================
    # Policy & Controls Tables
    # ============================================================================
    
    # Evidence Requirements table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence_requirements (
            requirement_id TEXT PRIMARY KEY,
            work_type TEXT,
            pricing_model TEXT,
            milestone_billing BOOLEAN,
            required_evidence_types TEXT,
            coverage_requirements TEXT,
            applicable_sow_id TEXT,
            FOREIGN KEY (applicable_sow_id) REFERENCES statements_of_work(sow_id)
        )
    """)
    
    # Anomaly Thresholds table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomaly_thresholds (
            threshold_id TEXT PRIMARY KEY,
            metric_type TEXT,
            vendor_id TEXT,
            baseline_value DECIMAL(10, 2),
            variance_percentage DECIMAL(5, 2),
            lookback_days INTEGER,
            FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
        )
    """)
    
    # ============================================================================
    # Invoice & Evidence Tables (File Tracking Only)
    # ============================================================================
    
    # Incoming Invoices table (file tracking + exception metadata)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incoming_invoices (
            invoice_id TEXT PRIMARY KEY,
            invoice_file_path TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            document_language TEXT DEFAULT 'en',
            submitted_at TIMESTAMP,
            scenario_type TEXT,
            exception_flags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Invoice Line Items table - NOT USED
    # Invoice line items are extracted from PDF by invoice extractor agent
    # Agents use extracted data directly to query/match against database (PO line items)
    # No need to store normalized invoice line items separately
    # Table kept for backward compatibility but not populated or queried
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_line_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id TEXT NOT NULL,
            line_number INTEGER,
            item_code TEXT,
            description TEXT,
            quantity DECIMAL(10, 2),
            unit_price DECIMAL(10, 2),
            total DECIMAL(10, 2),
            cost_category TEXT,
            classification_confidence DECIMAL(3, 2),
            extracted_at TIMESTAMP,
            FOREIGN KEY (invoice_id) REFERENCES incoming_invoices(invoice_id)
        )
    """)
    
    # Evidence Documents table (file tracking only)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence_documents (
            evidence_id TEXT PRIMARY KEY,
            invoice_id TEXT,
            evidence_file_path TEXT NOT NULL,
            evidence_type TEXT,
            document_language TEXT DEFAULT 'en',
            submitted_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (invoice_id) REFERENCES incoming_invoices(invoice_id)
        )
    """)
    
    # ============================================================================
    # AI / Agent Operations Tables
    # ============================================================================
    
    # Validation Results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS validation_results (
            validation_id TEXT PRIMARY KEY,
            invoice_id TEXT NOT NULL,
            validation_type TEXT,
            validation_status TEXT,
            checked_value TEXT,
            expected_value TEXT,
            variance DECIMAL(10, 2),
            validation_details TEXT,
            validated_at TIMESTAMP,
            validated_by_agent TEXT,
            FOREIGN KEY (invoice_id) REFERENCES incoming_invoices(invoice_id)
        )
    """)
    
    # Exceptions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exceptions (
            exception_id TEXT PRIMARY KEY,
            invoice_id TEXT NOT NULL,
            exception_type TEXT,
            exception_category TEXT,
            severity TEXT,
            exception_description TEXT,
            evidence_found TEXT,
            recommended_action TEXT,
            detected_at TIMESTAMP,
            detected_by_agent TEXT,
            FOREIGN KEY (invoice_id) REFERENCES incoming_invoices(invoice_id)
        )
    """)
    
    # Cost Classifications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cost_classifications (
            classification_id TEXT PRIMARY KEY,
            invoice_id TEXT NOT NULL,
            line_item_id INTEGER,
            cost_category TEXT,
            cost_subcategory TEXT,
            classification_confidence DECIMAL(3, 2),
            classification_rules_applied TEXT,
            classified_at TIMESTAMP,
            FOREIGN KEY (invoice_id) REFERENCES incoming_invoices(invoice_id)
        )
    """)
    
    # Invoice Processing Status table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_processing_status (
            status_id TEXT PRIMARY KEY,
            invoice_id TEXT UNIQUE NOT NULL,
            run_id TEXT,
            processing_status TEXT,
            final_decision TEXT,
            decision_rationale TEXT,
            straight_through_eligible BOOLEAN,
            requires_human_review BOOLEAN,
            review_reason TEXT,
            processed_at TIMESTAMP,
            decision_made_at TIMESTAMP,
            FOREIGN KEY (invoice_id) REFERENCES incoming_invoices(invoice_id)
        )
    """)
    
    # Add run_id column to existing tables (migration for existing databases)
    try:
        cursor.execute("ALTER TABLE invoice_processing_status ADD COLUMN run_id TEXT")
    except Exception:
        # Column already exists, ignore
        pass
    
    # Add updated_at column to incoming_invoices table (migration for existing databases)
    try:
        cursor.execute("ALTER TABLE incoming_invoices ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except Exception:
        # Column already exists, ignore
        pass
    
    # Add scenario_type and exception_flags columns to incoming_invoices table (migration for existing databases)
    try:
        cursor.execute("ALTER TABLE incoming_invoices ADD COLUMN scenario_type TEXT")
    except Exception:
        # Column already exists, ignore
        pass
    
    try:
        cursor.execute("ALTER TABLE incoming_invoices ADD COLUMN exception_flags TEXT")
    except Exception:
        # Column already exists, ignore
        pass
    
    # Historical Invoices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historical_invoices (
            historical_id TEXT PRIMARY KEY,
            invoice_number TEXT,
            vendor_id TEXT,
            invoice_date DATE,
            total_amount DECIMAL(10, 2),
            po_number TEXT,
            sow_id TEXT,
            final_status TEXT,
            payment_date DATE,
            payment_amount DECIMAL(10, 2),
            exceptions_detected TEXT,
            processing_time_hours DECIMAL(5, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
        )
    """)
    
    # ============================================================================
    # HITL Operations Tables
    # ============================================================================
    
    # Clarification Requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clarification_requests (
            request_id TEXT PRIMARY KEY,
            invoice_id TEXT NOT NULL,
            vendor_id TEXT,
            invoice_number TEXT,
            request_type TEXT NOT NULL,
            required_information TEXT,
            requested_evidence_types TEXT,
            status TEXT DEFAULT 'pending',
            requested_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            responded_date TIMESTAMP,
            response_details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (invoice_id) REFERENCES incoming_invoices(invoice_id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
        )
    """)
    
    # Finance Adjustments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finance_adjustments (
            adjustment_id TEXT PRIMARY KEY,
            invoice_id TEXT NOT NULL,
            vendor_id TEXT,
            invoice_number TEXT,
            adjustment_type TEXT NOT NULL,
            adjustment_amount DECIMAL(10, 2) NOT NULL,
            adjustment_reason TEXT,
            original_invoice_amount DECIMAL(10, 2),
            adjusted_invoice_amount DECIMAL(10, 2),
            retention_percentage DECIMAL(5, 2),
            ld_rate_per_day DECIMAL(10, 2),
            ld_days INTEGER,
            milestone_id TEXT,
            sow_id TEXT,
            status TEXT DEFAULT 'pending',
            finance_team_notes TEXT,
            applied_date TIMESTAMP,
            applied_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (invoice_id) REFERENCES incoming_invoices(invoice_id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
            FOREIGN KEY (milestone_id) REFERENCES milestones(milestone_id),
            FOREIGN KEY (sow_id) REFERENCES statements_of_work(sow_id)
        )
    """)
    
    # ============================================================================
    # Create Indexes
    # ============================================================================
    
    # ERP indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendors_code ON vendors(vendor_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pos_vendor ON purchase_orders(vendor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pos_sow ON purchase_orders(sow_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pos_project ON purchase_orders(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_items_po ON po_line_items(po_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_po_items_wbs ON po_line_items(wbs_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_vendor ON payment_history(vendor_id)")
    
    # Contract indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sows_invoice_type ON statements_of_work(invoice_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sows_vendor ON statements_of_work(vendor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rate_cards_vendor ON rate_cards(vendor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rate_cards_sow ON rate_cards(sow_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commercial_terms_sow ON commercial_terms(sow_id)")
    
    # Project indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wbs_project ON work_breakdown_structure(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wbs_parent ON work_breakdown_structure(parent_wbs_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_milestones_project ON milestones(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_milestones_sow ON milestones(sow_id)")
    
    # Policy indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_req_sow ON evidence_requirements(applicable_sow_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_anomaly_vendor ON anomaly_thresholds(vendor_id)")
    
    # Invoice indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_status ON incoming_invoices(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_invoice ON evidence_documents(invoice_id)")
    
    # Agent operations indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_validation_invoice ON validation_results(invoice_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exceptions_invoice ON exceptions(invoice_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_classifications_invoice ON cost_classifications(invoice_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status_invoice ON invoice_processing_status(invoice_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status_run ON invoice_processing_status(run_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historical_vendor ON historical_invoices(vendor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historical_date ON historical_invoices(invoice_date)")
    
    # HITL operations indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clarification_invoice ON clarification_requests(invoice_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clarification_vendor ON clarification_requests(vendor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clarification_status ON clarification_requests(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_adjustment_invoice ON finance_adjustments(invoice_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_adjustment_vendor ON finance_adjustments(vendor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_adjustment_status ON finance_adjustments(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_adjustment_type ON finance_adjustments(adjustment_type)")
    
    conn.commit()
    conn.close()
    print("✓ Database schema created")


# ============================================================================
# Foundation Data Generation
# ============================================================================

def generate_mock_vendors(cursor, count: int = 12) -> List[Dict[str, Any]]:
    """Generate mock vendors for oil & gas industry."""
    vendor_names = [
        "Offshore Drilling Services Inc",
        "PetroLogistics Solutions",
        "Marine Engineering Corp",
        "Rig Maintenance Specialists",
        "Pipeline Construction Group",
        "Well Completion Services",
        "Subsea Equipment Suppliers",
        "Vessel Operations Ltd",
        "Safety & Compliance Partners",
        "Environmental Services Co",
        "Equipment Rental Solutions",
        "Technical Consulting Group",
        "Crane & Lifting Services",
        "Catering & Logistics Pro",
        "Inspection & Testing Services"
    ]
    
    payment_terms_options = ["Net 30", "Net 45", "Net 60", "2/10 Net 30", "1/15 Net 45"]
    
    vendors = []
    selected_names = random.sample(vendor_names, min(count, len(vendor_names)))
    
    for i, vendor_name in enumerate(selected_names):
        vendor_id = f"VEND-{i+1:03d}"
        vendor_code = f"V{1000 + i:04d}"
        tax_id = f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}"
        payment_terms = random.choice(payment_terms_options)
        
        cursor.execute("""
            INSERT INTO vendors (vendor_id, vendor_name, vendor_code, tax_id, payment_terms, currency, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (vendor_id, vendor_name, vendor_code, tax_id, payment_terms, "GBP", "active"))
        
        vendors.append({
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "vendor_code": vendor_code
        })
    
    print(f"  ✓ Generated {len(vendors)} vendors")
    return vendors


def generate_mock_projects(cursor, count: int = 6) -> List[Dict[str, Any]]:
    """Generate mock oil & gas projects."""
    project_types = ["drilling", "production", "maintenance", "construction", "decommissioning"]
    
    project_names = [
        "North Sea Platform Alpha",
        "Gulf of Mexico Deepwater Drilling",
        "Permian Basin Production Enhancement",
        "Offshore Pipeline Installation",
        "Well Completion & Testing",
        "Platform Maintenance & Upgrade",
        "Subsea Infrastructure Development",
        "Refinery Expansion Project"
    ]
    
    projects = []
    base_date = datetime.now() - timedelta(days=730)  # 2 years ago
    
    for i in range(count):
        project_id = f"PROJ-{i+1:03d}"
        project_code = f"PRJ{datetime.now().year - 3 + i:04d}"  # Use current year minus 3 as base
        project_name = project_names[i] if i < len(project_names) else f"Project {i+1}"
        project_type = random.choice(project_types)
        
        start_date = base_date + timedelta(days=random.randint(0, 400))
        end_date = start_date + timedelta(days=random.randint(180, 720))
        budget = random.uniform(5000000, 50000000)
        
        cursor.execute("""
            INSERT INTO projects (project_id, project_code, project_name, project_type, status, start_date, end_date, budget)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (project_id, project_code, project_name, project_type, "active", 
              start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), round(budget, 2)))
        
        projects.append({
            "project_id": project_id,
            "project_code": project_code,
            "project_name": project_name,
            "project_type": project_type,
            "start_date": start_date,
            "end_date": end_date,
            "budget": budget
        })
    
    print(f"  ✓ Generated {len(projects)} projects")
    return projects


def generate_mock_wbs(cursor, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate mock WBS structures (2-3 levels per project)."""
    wbs_templates = {
        "drilling": [
            ("Site Preparation", ["Survey & Mapping", "Access Roads", "Site Clearing"]),
            ("Drilling Operations", ["Rig Setup", "Drilling", "Casing & Cementing"]),
            ("Completion", ["Well Testing", "Production Equipment", "Handover"])
        ],
        "production": [
            ("Facilities", ["Platform Construction", "Processing Equipment", "Utilities"]),
            ("Operations", ["Production Start", "Maintenance", "Monitoring"]),
            ("Support", ["Logistics", "Safety Systems", "Environmental"])
        ],
        "maintenance": [
            ("Inspection", ["Visual Inspection", "NDT Testing", "Structural Assessment"]),
            ("Repairs", ["Equipment Replacement", "Structural Repairs", "System Updates"]),
            ("Commissioning", ["Testing", "Certification", "Documentation"])
        ],
        "construction": [
            ("Engineering", ["Design", "Procurement", "Fabrication"]),
            ("Installation", ["Transportation", "Installation", "Hook-up"]),
            ("Commissioning", ["Testing", "Start-up", "Handover"])
        ],
        "decommissioning": [
            ("Planning", ["Assessment", "Permits", "Planning"]),
            ("Execution", ["Equipment Removal", "Platform Removal", "Site Cleanup"]),
            ("Closure", ["Verification", "Reporting", "Final Closure"])
        ]
    }
    
    all_wbs = []
    wbs_counter = 1
    
    for project in projects:
        project_type = project["project_type"]
        template = wbs_templates.get(project_type, wbs_templates["drilling"])
        
        # Level 1 WBS
        for level1_name, level2_items in template:
            wbs_id = f"WBS-{wbs_counter:04d}"
            wbs_code = f"{project['project_code']}-{wbs_counter:02d}"
            wbs_counter += 1
            
            cursor.execute("""
                INSERT INTO work_breakdown_structure 
                (wbs_id, wbs_code, project_id, parent_wbs_id, wbs_name, wbs_level, budget_allocation, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (wbs_id, wbs_code, project["project_id"], None, level1_name, 1, 
                  round(project["budget"] * random.uniform(0.2, 0.4), 2), "active"))
            
            level1_wbs = {
                "wbs_id": wbs_id,
                "wbs_code": wbs_code,
                "project_id": project["project_id"],
                "wbs_name": level1_name,
                "level": 1
            }
            all_wbs.append(level1_wbs)
            
            # Level 2 WBS (2-3 items per level 1)
            selected_items = random.sample(level2_items, min(random.randint(2, 3), len(level2_items)))
            for level2_name in selected_items:
                wbs_id_2 = f"WBS-{wbs_counter:04d}"
                wbs_code_2 = f"{wbs_code}-{len(selected_items) - selected_items.index(level2_name) + 1:02d}"
                wbs_counter += 1
                
                cursor.execute("""
                    INSERT INTO work_breakdown_structure 
                    (wbs_id, wbs_code, project_id, parent_wbs_id, wbs_name, wbs_level, budget_allocation, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (wbs_id_2, wbs_code_2, project["project_id"], level1_wbs["wbs_id"], level2_name, 2,
                      round(project["budget"] * random.uniform(0.05, 0.15), 2), "active"))
                
                all_wbs.append({
                    "wbs_id": wbs_id_2,
                    "wbs_code": wbs_code_2,
                    "project_id": project["project_id"],
                    "wbs_name": level2_name,
                    "level": 2
                })
    
    print(f"  ✓ Generated {len(all_wbs)} WBS entries")
    return all_wbs


def generate_mock_rate_cards(cursor, vendors: List[Dict[str, Any]], sows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate mock rate cards for vendors/SOWs.
    
    Rate cards use item codes that match PO line items (LAB-001, LAB-002, MAT-001, etc.)
    to ensure validation can match invoice items to rate cards.
    """
    # Labor roles and rates (matching PO generation)
    labor_roles = ["Project Manager", "Senior Engineer", "Engineer", "Technician", "Supervisor"]
    labor_rates = [150.0, 120.0, 95.0, 75.0, 110.0]
    
    # Material categories (matching PO generation)
    material_categories = ["Steel", "Valves", "Piping", "Electrical", "Instrumentation", "Civil"]
    material_descriptions = ["Pipe", "Valve", "Fitting", "Component"]
    
    rate_cards = []
    
    for sow in sows:
        vendor_id = sow.get("vendor_id")
        sow_id = sow["sow_id"]
        invoice_type = sow.get("invoice_type", "PROFORMA")
        
        # Generate rate cards based on invoice type, matching PO line item patterns
        # Generate 5-10 rate card items per SOW to cover various PO line items
        num_items = random.randint(5, 10)
        
        for i in range(1, num_items + 1):
            # Generate item codes matching PO line item pattern (LAB-001, LAB-002, MAT-001, etc.)
            if invoice_type == "LABOR":
                item_code = f"LAB-{i:03d}"
                role = random.choice(labor_roles)
                description = f"{role} - Engineering Design Services"
                unit = "hour"
                # Use role-based rate range
                role_index = labor_roles.index(role)
                base_rate = labor_rates[role_index]
                min_price = base_rate * 0.9
                max_price = base_rate * 1.1
            elif invoice_type == "MATERIAL":
                item_code = f"MAT-{i:03d}"
                material_cat = random.choice(material_categories)
                material_desc = random.choice(material_descriptions)
                description = f"{material_cat} - {material_desc}"
                unit = "each"
                min_price = 50.00
                max_price = 500.00
            else:  # PROFORMA - mix of labor and material
                if random.random() < 0.5:  # 50% labor, 50% material
                    item_code = f"LAB-{i:03d}"
                    role = random.choice(labor_roles)
                    description = f"{role} - Safety Compliance Services"
                    unit = "hour"
                    role_index = labor_roles.index(role)
                    base_rate = labor_rates[role_index]
                    min_price = base_rate * 0.9
                    max_price = base_rate * 1.1
                else:
                    item_code = f"MAT-{i:03d}"
                    material_cat = random.choice(material_categories)
                    material_desc = random.choice(material_descriptions)
                    description = f"{material_cat} - {material_desc}"
                    unit = "each"
                    min_price = 50.00
                    max_price = 500.00
            rate_card_id = f"RATE-{uuid.uuid4().hex[:8].upper()}"
            unit_price = round(random.uniform(min_price, max_price), 2)
            effective_date = sow.get("start_date", datetime.now() - timedelta(days=90))
            expiry_date = sow.get("end_date", datetime.now() + timedelta(days=365))
            
            cursor.execute("""
                INSERT INTO rate_cards 
                (rate_card_id, vendor_id, sow_id, item_code, description, unit_price, unit_of_measure, 
                 effective_date, expiry_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (rate_card_id, vendor_id, sow_id, item_code, description, unit_price, unit,
                  effective_date.strftime("%Y-%m-%d") if isinstance(effective_date, datetime) else effective_date,
                  expiry_date.strftime("%Y-%m-%d") if isinstance(expiry_date, datetime) else expiry_date,
                  "active"))
            
            rate_cards.append({
                "rate_card_id": rate_card_id,
                "sow_id": sow_id,
                "item_code": item_code,
                "unit_price": unit_price
            })
    
    print(f"  ✓ Generated {len(rate_cards)} rate card entries")
    return rate_cards


def generate_mock_evidence_requirements(cursor, sows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate mock evidence requirements based on invoice type."""
    pricing_models = ["time_materials", "fixed_price", "milestone_based"]
    # Evidence types map by invoice type
    evidence_types_map = {
        "LABOR": ["timesheet"],
        "MATERIAL": ["grn"],
        "PROFORMA": ["timesheet", "completion_certificate", "grn"]
    }
    
    requirements = []
    
    for sow in sows:
        sow_id = sow["sow_id"]
        invoice_type = sow.get("invoice_type", "PROFORMA")
        pricing_model = sow.get("pricing_model", random.choice(pricing_models))
        
        # Get required evidence types for this invoice type
        required_evidence = evidence_types_map.get(invoice_type, ["timesheet", "completion_certificate", "grn"])
        milestone_billing = pricing_model == "milestone_based"
        
        # Generate one requirement per SOW (based on invoice type, not work type)
        requirement_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
        
        coverage_req = {
            "date_range_required": True,
            "quantity_verification": invoice_type in ["LABOR", "MATERIAL"],  # Verify quantities for labor and material
            "approval_required": milestone_billing
        }
        
        cursor.execute("""
            INSERT INTO evidence_requirements 
            (requirement_id, work_type, pricing_model, milestone_billing, 
             required_evidence_types, coverage_requirements, applicable_sow_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (requirement_id, invoice_type, pricing_model, milestone_billing,
              json.dumps(required_evidence), json.dumps(coverage_req), sow_id))
        
        requirements.append({
            "requirement_id": requirement_id,
            "sow_id": sow_id,
            "invoice_type": invoice_type
        })
    
    print(f"  ✓ Generated {len(requirements)} evidence requirements")
    return requirements


# ============================================================================
# Contractual Data Generation
# ============================================================================

def generate_mock_pos(cursor, vendors: List[Dict[str, Any]], projects: List[Dict[str, Any]], 
                      wbs_list: List[Dict[str, Any]], sows: List[Dict[str, Any]], count: int = 25) -> List[Dict[str, Any]]:
    """Generate mock Purchase Orders linked to SOWs with WBS assignments on PO lines."""
    pos = []
    base_date = datetime.now() - timedelta(days=180)
    current_year = datetime.now().year
    
    # Labor roles and rates
    labor_roles = ["Project Manager", "Senior Engineer", "Engineer", "Technician", "Supervisor"]
    labor_rates = [150.0, 120.0, 95.0, 75.0, 110.0]
    
    # Material categories
    material_categories = ["Steel", "Valves", "Piping", "Electrical", "Instrumentation", "Civil"]
    
    for i in range(count):
        po_number = f"PO-{current_year}-{1000 + i:04d}"
        # Link PO to a SOW
        sow = random.choice(sows)
        sow_id = sow["sow_id"]
        vendor_id = sow["vendor_id"]
        project_id = sow["project_id"]
        invoice_type = sow.get("invoice_type", "PROFORMA")
        
        # Get vendor and project
        vendor = next((v for v in vendors if v["vendor_id"] == vendor_id), None)
        project = next((p for p in projects if p["project_id"] == project_id), None)
        if not vendor or not project:
            continue
        
        # Get WBS elements for this project
        project_wbs = [w for w in wbs_list if w["project_id"] == project_id]
        if not project_wbs:
            continue
        
        po_date = base_date + timedelta(days=random.randint(0, 150))
        
        # Generate line items based on invoice type
        num_items = random.randint(2, 5)
        total_amount = 0.0
        line_items = []
        
        for line_num in range(1, num_items + 1):
            # Assign WBS to each line item
            wbs = random.choice(project_wbs)
            wbs_id = wbs["wbs_id"]
            
            quantity = random.uniform(10, 100)
            unit_price = random.uniform(50, 500)
            line_total = round(quantity * unit_price, 2)
            total_amount += line_total
            
            # Generate item based on invoice type
            if invoice_type == "LABOR":
                role = random.choice(labor_roles)
                rate = random.choice(labor_rates)
                item_code = f"LAB-{line_num:03d}"
                description = f"{role} - {random.randint(40, 160)} hours"
                material_category = None
            elif invoice_type == "MATERIAL":
                role = None
                rate = None
                material_cat = random.choice(material_categories)
                item_code = f"MAT-{line_num:03d}"
                description = f"{material_cat} - {random.choice(['Pipe', 'Valve', 'Fitting', 'Component'])}"
                material_category = material_cat
            else:  # PROFORMA - mix of labor and material
                if random.random() < 0.5:  # 50% labor, 50% material
                    role = random.choice(labor_roles)
                    rate = random.choice(labor_rates)
                    item_code = f"LAB-{line_num:03d}"
                    description = f"{role} - {random.randint(40, 160)} hours"
                    material_category = None
                else:
                    role = None
                    rate = None
                    material_cat = random.choice(material_categories)
                    item_code = f"MAT-{line_num:03d}"
                    description = f"{material_cat} - {random.choice(['Pipe', 'Valve', 'Fitting', 'Component'])}"
                    material_category = material_cat
            
            line_items.append({
                "line_number": line_num,
                "item_code": item_code,
                "description": description,
                "quantity": quantity,
                "unit_price": unit_price,
                "total": line_total,
                "wbs_id": wbs_id,
                "role": role,
                "rate": rate,
                "material_category": material_category
            })
        
        cursor.execute("""
            INSERT INTO purchase_orders 
            (po_number, vendor_id, sow_id, po_date, status, total_amount, currency, project_id, approver)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (po_number, vendor_id, sow_id, po_date.strftime("%Y-%m-%d"), "approved",
              round(total_amount, 2), "GBP", project_id, "John Smith"))
        
        # Insert line items with WBS, role, rate assignments
        for item in line_items:
            cursor.execute("""
                INSERT INTO po_line_items 
                (po_number, line_number, item_code, description, quantity, unit_price, total, wbs_id, role, rate, material_category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (po_number, item["line_number"], item["item_code"], item["description"],
                  item["quantity"], item["unit_price"], item["total"], item["wbs_id"],
                  item["role"], item["rate"], item["material_category"]))
        
        pos.append({
            "po_number": po_number,
            "vendor_id": vendor_id,
            "sow_id": sow_id,
            "project_id": project_id,
            "total_amount": total_amount,
            "po_date": po_date
        })
    
    print(f"  ✓ Generated {len(pos)} Purchase Orders")
    return pos


def read_sow_terms_from_global_memory(project_dir: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """Read SOW terms from global memory.
    
    Returns: Dict mapping sow_number -> sow_terms dict
        Example: {
            "SOW-2026-2891": {
                "sow_number": "SOW-2026-2891",
                "retention_percentage": 5.0,
                "ld_applicable": True,
                "ld_rate_per_day": 500.0,
                "milestones": [...],
                "rate_cards": [...],
                "effective_date": "2026-01-25",
                "status": "active"
            }
        }
    """
    if not project_dir:
        return {}
    
    global_memory_file = project_dir / "data" / "agentos" / "global_shared" / "contracts" / "sow_terms.jsonl"
    
    if not global_memory_file.exists():
        return {}
    
    sow_terms_map = {}
    try:
        with open(global_memory_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    sow_data = json.loads(line)
                    sow_number = sow_data.get("sow_number")
                    if sow_number:
                        # If multiple entries for same SOW, keep the latest (by effective_date)
                        if sow_number not in sow_terms_map:
                            sow_terms_map[sow_number] = sow_data
                        else:
                            # Compare effective_date to keep the latest
                            existing_date = sow_terms_map[sow_number].get("effective_date", "")
                            new_date = sow_data.get("effective_date", "")
                            if new_date > existing_date:
                                sow_terms_map[sow_number] = sow_data
    except Exception as e:
        print(f"  ⚠ Warning: Failed to read SOW terms from global memory: {e}")
        return {}
    
    return sow_terms_map


def read_sow_metadata_from_global_memory(project_dir: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """Read SOW metadata from global memory.
    
    Returns: Dict mapping sow_number -> sow_metadata dict
        Example: {
            "SOW-2026-2891": {
                "sow_number": "SOW-2026-2891",
                "invoice_type": "PROFORMA",
                "vendor_name": "Service Provider Corporation",
                "pricing_model": "milestone_based",
                "effective_date": "2026-01-25",
                "status": "active"
            }
        }
    """
    if not project_dir:
        return {}
    
    global_memory_file = project_dir / "data" / "agentos" / "global_shared" / "contracts" / "sow_metadata.jsonl"
    
    if not global_memory_file.exists():
        return {}
    
    sow_metadata_map = {}
    try:
        with open(global_memory_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    metadata = json.loads(line)
                    sow_number = metadata.get("sow_number")
                    if sow_number:
                        # If multiple entries for same SOW, keep the latest (by effective_date)
                        if sow_number not in sow_metadata_map:
                            sow_metadata_map[sow_number] = metadata
                        else:
                            # Compare effective_date to keep the latest
                            existing_date = sow_metadata_map[sow_number].get("effective_date", "")
                            new_date = metadata.get("effective_date", "")
                            if new_date > existing_date:
                                sow_metadata_map[sow_number] = metadata
    except Exception as e:
        print(f"  ⚠ Warning: Failed to read SOW metadata from global memory: {e}")
        return {}
    
    return sow_metadata_map


def generate_mock_sows(cursor, vendors: List[Dict[str, Any]],
                       projects: List[Dict[str, Any]], count: int = 20,
                       invoice_type_dist: Optional[Dict[str, float]] = None,
                       sow_terms_from_global: Optional[Dict[str, Dict[str, Any]]] = None,
                       sow_metadata_from_global: Optional[Dict[str, Dict[str, Any]]] = None,
                       global_memory_only: bool = False) -> tuple[List[Dict[str, Any]], Dict[str, bool]]:
    """Generate mock Statements of Work with invoice type classification.
    
    Args:
        invoice_type_dist: Dictionary with invoice type distribution percentages.
            Default: {"LABOR": 0.4, "MATERIAL": 0.4, "PROFORMA": 0.2}
    """
    pricing_models = ["time_materials", "fixed_price", "milestone_based"]
    
    # Default distribution: 40% Labor, 40% Material, 20% Proforma
    if invoice_type_dist is None:
        invoice_type_dist = {"LABOR": 0.4, "MATERIAL": 0.4, "PROFORMA": 0.2}
    
    # Normalize distribution to ensure it sums to 1.0
    total = sum(invoice_type_dist.values())
    if total > 0:
        invoice_type_dist = {k: v / total for k, v in invoice_type_dist.items()}
    else:
        invoice_type_dist = {"LABOR": 0.4, "MATERIAL": 0.4, "PROFORMA": 0.2}
    
    # Create list of invoice types based on distribution
    invoice_types_list = []
    labor_count = max(1, round(count * invoice_type_dist.get("LABOR", 0.4)))
    material_count = max(1, round(count * invoice_type_dist.get("MATERIAL", 0.4)))
    proforma_count = count - labor_count - material_count  # Remaining goes to Proforma
    
    invoice_types_list.extend(["LABOR"] * labor_count)
    invoice_types_list.extend(["MATERIAL"] * material_count)
    invoice_types_list.extend(["PROFORMA"] * proforma_count)
    
    # Shuffle to randomize order
    random.shuffle(invoice_types_list)
    
    sows = []
    base_date = datetime.now() - timedelta(days=120)
    current_year = datetime.now().year
    sow_global_memory_usage = {}  # Track which SOWs used global memory: {sow_number: bool}
    
    # Get list of SOW numbers from global memory if available
    global_sow_numbers = list(sow_terms_from_global.keys()) if sow_terms_from_global else []
    
    # If global_memory_only is True, only generate SOWs from global memory
    if global_memory_only:
        if not global_sow_numbers:
            print(f"  ⚠ Warning: global_memory_only=True but no SOWs found in global memory. Cannot generate SOWs.")
            return [], {}
        # Limit count to available global memory SOWs
        actual_count = min(count, len(global_sow_numbers))
        if actual_count < count:
            print(f"  ⚠ Warning: Requested {count} SOWs but only {len(global_sow_numbers)} available in global memory. Generating {actual_count} SOWs.")
        count = actual_count
    
    for i in range(count):
        sow_id = f"SOW-{uuid.uuid4().hex[:8].upper()}"
        
        # Check if we should use a SOW number from global memory
        used_global_memory = False
        if global_sow_numbers and i < len(global_sow_numbers):
            # Use SOW number from global memory
            sow_number = global_sow_numbers[i]
            sow_terms = sow_terms_from_global[sow_number]
            used_global_memory = True
        elif global_memory_only:
            # If global_memory_only is True but we've exhausted global memory SOWs, skip
            print(f"  ⚠ Warning: global_memory_only=True but only {len(global_sow_numbers)} SOWs available. Skipping remaining SOWs.")
            break
        else:
            # Generate new SOW number
            sow_number = f"SOW-{current_year}-{2000 + i:04d}"
        
        vendor = random.choice(vendors)
        vendor_id = vendor["vendor_id"]
        project = random.choice(projects)
        project_id = project["project_id"]
        
        # Classify SOW by invoice type
        # Priority 1: Use invoice_type from global memory metadata if available
        # Priority 2: Use distribution-based invoice type
        if used_global_memory and sow_metadata_from_global and sow_number in sow_metadata_from_global:
            invoice_type = sow_metadata_from_global[sow_number].get("invoice_type")
            if invoice_type not in ["LABOR", "MATERIAL", "PROFORMA"]:
                # Invalid invoice type, fall back to distribution
                invoice_type = invoice_types_list[i] if i < len(invoice_types_list) else random.choice(["LABOR", "MATERIAL", "PROFORMA"])
        else:
            # Use distribution-based invoice type
            invoice_type = invoice_types_list[i] if i < len(invoice_types_list) else random.choice(["LABOR", "MATERIAL", "PROFORMA"])
        
        # Use pricing model from global memory metadata if available, otherwise infer from milestones or random
        if used_global_memory and sow_metadata_from_global and sow_number in sow_metadata_from_global:
            pricing_model = sow_metadata_from_global[sow_number].get("pricing_model")
            if pricing_model not in pricing_models:
                # Invalid pricing model, infer from milestones or random
                pricing_model = "milestone_based" if sow_terms.get("milestones") else random.choice(pricing_models)
        elif used_global_memory and sow_terms.get("milestones"):
            pricing_model = "milestone_based"
        else:
            pricing_model = random.choice(pricing_models)
        
        # Commercial terms: Use from global memory if available, otherwise generate randomly
        if used_global_memory:
            retention_percentage = sow_terms.get("retention_percentage")
            if retention_percentage is None:
                retention_percentage = 0
            else:
                retention_percentage = float(retention_percentage)
            
            ld_applicable = sow_terms.get("ld_applicable")
            if ld_applicable is None:
                ld_applicable = False
            
            ld_rate = sow_terms.get("ld_rate_per_day")
            if ld_rate is not None:
                ld_rate = float(ld_rate)
            elif ld_applicable:
                ld_rate = round(random.uniform(500, 2000), 2)
            else:
                ld_rate = None
        else:
            # Generate randomly
            retention_percentage = random.choice([0, 5, 10]) if pricing_model != "milestone_based" else 0
            ld_applicable = random.choice([True, False])
            ld_rate = round(random.uniform(500, 2000), 2) if ld_applicable else None
        
        # Dates: Use effective_date from global memory if available, otherwise generate
        if used_global_memory and sow_terms.get("effective_date"):
            try:
                effective_date = datetime.strptime(sow_terms["effective_date"], "%Y-%m-%d")
                start_date = effective_date - timedelta(days=random.randint(0, 30))
                end_date = start_date + timedelta(days=random.randint(90, 365))
            except (ValueError, KeyError):
                start_date = base_date + timedelta(days=random.randint(0, 60))
                end_date = start_date + timedelta(days=random.randint(90, 365))
        else:
            start_date = base_date + timedelta(days=random.randint(0, 60))
            end_date = start_date + timedelta(days=random.randint(90, 365))
        
        # Generate SOW total amount (independent of POs)
        sow_total = round(random.uniform(50000, 500000), 2)
        retention_held = round(sow_total * (retention_percentage / 100), 2) if retention_percentage > 0 else 0
        
        # Track global memory usage
        sow_global_memory_usage[sow_number] = used_global_memory
        
        cursor.execute("""
            INSERT INTO statements_of_work 
            (sow_id, sow_number, vendor_id, project_id, invoice_type, pricing_model,
             retention_percentage, retention_held, ld_applicable, ld_rate_per_day,
             start_date, end_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (sow_id, sow_number, vendor_id, project_id, invoice_type, pricing_model,
              retention_percentage, retention_held, ld_applicable, ld_rate,
              start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), "active"))
        
        # Add commercial terms
        if retention_percentage > 0:
            term_id = f"TERM-{uuid.uuid4().hex[:8].upper()}"
            cursor.execute("""
                INSERT INTO commercial_terms 
                (term_id, sow_id, term_type, term_value, applicable_from, applicable_to)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (term_id, sow_id, "retention", json.dumps({"percentage": retention_percentage}),
                  start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
        
        if ld_applicable:
            term_id = f"TERM-{uuid.uuid4().hex[:8].upper()}"
            cursor.execute("""
                INSERT INTO commercial_terms 
                (term_id, sow_id, term_type, term_value, applicable_from, applicable_to)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (term_id, sow_id, "ld", json.dumps({"rate_per_day": ld_rate}),
                  start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
        
        sows.append({
            "sow_id": sow_id,
            "sow_number": sow_number,
            "vendor_id": vendor_id,
            "project_id": project_id,
            "invoice_type": invoice_type,
            "pricing_model": pricing_model,
            "retention_percentage": retention_percentage,
            "ld_applicable": ld_applicable,
            "ld_rate": ld_rate,
            "start_date": start_date,
            "end_date": end_date,
            "used_global_memory": used_global_memory
        })
    
    # Count how many used global memory
    global_count = sum(1 for v in sow_global_memory_usage.values() if v)
    if global_count > 0:
        print(f"  ✓ Generated {len(sows)} Statements of Work ({global_count} from global memory, {len(sows) - global_count} generated)")
    else:
        print(f"  ✓ Generated {len(sows)} Statements of Work (all generated, none from global memory)")
    
    return sows, sow_global_memory_usage


def generate_mock_milestones(cursor, sows: List[Dict[str, Any]], projects: List[Dict[str, Any]],
                            sow_terms_from_global: Optional[Dict[str, Dict[str, Any]]] = None) -> tuple[List[Dict[str, Any]], Dict[str, bool]]:
    """Generate mock milestones (3-5 per SOW for milestone-based SOWs).
    
    Returns: (milestones_list, milestone_global_memory_usage_dict)
    """
    milestones = []
    milestone_types = ["approval", "completion", "payment"]
    milestone_global_memory_usage = {}  # Track which milestones used global memory: {sow_number: bool}
    
    for sow in sows:
        if sow["pricing_model"] != "milestone_based":
            continue
        
        project_id = sow["project_id"]
        sow_id = sow["sow_id"]
        sow_number = sow["sow_number"]
        
        # Check if milestones are available in global memory
        used_global_memory = False
        global_milestones = None
        if sow_terms_from_global and sow_number in sow_terms_from_global:
            global_milestones = sow_terms_from_global[sow_number].get("milestones", [])
            if global_milestones:
                used_global_memory = True
        
        # Get project WBS codes
        cursor.execute("""
            SELECT wbs_id, wbs_code FROM work_breakdown_structure 
            WHERE project_id = ? AND wbs_level = 2
            LIMIT 3
        """, (project_id,))
        wbs_options = cursor.fetchall()
        
        start_date = sow["start_date"]
        end_date = sow["end_date"]
        
        if used_global_memory and global_milestones:
            # Use milestones from global memory
            num_milestones = len(global_milestones)
            for i, global_milestone in enumerate(global_milestones):
                milestone_id = f"MIL-{uuid.uuid4().hex[:8].upper()}"
                milestone_code = f"MS-{sow_number}-{i+1:02d}"
                
                # Extract milestone data from global memory
                milestone_name = global_milestone.get("name", f"Milestone {i+1}")
                milestone_type = global_milestone.get("type", random.choice(milestone_types))
                
                # Use milestone_due from global memory if available, otherwise calculate
                if global_milestone.get("milestone_due"):
                    try:
                        planned_date = datetime.strptime(global_milestone["milestone_due"], "%Y-%m-%d")
                    except (ValueError, KeyError):
                        duration_days = (end_date - start_date).days
                        milestone_interval = duration_days // (num_milestones + 1)
                        planned_date = start_date + timedelta(days=(i + 1) * milestone_interval)
                else:
                    duration_days = (end_date - start_date).days
                    milestone_interval = duration_days // (num_milestones + 1)
                    planned_date = start_date + timedelta(days=(i + 1) * milestone_interval)
                
                # Actual date: random variation if milestone is completed
                actual_date = planned_date + timedelta(days=random.randint(-5, 10)) if random.random() > 0.3 else None
                
                milestone_cap = global_milestone.get("cap_amount")
                if milestone_cap is None:
                    milestone_cap = round(random.uniform(50000, 200000), 2)
                else:
                    milestone_cap = float(milestone_cap)
                
                approval_status = "approved" if actual_date and actual_date <= planned_date + timedelta(days=5) else "pending"
                
                wbs_id = random.choice(wbs_options)[0] if wbs_options else None
                
                cursor.execute("""
                    INSERT INTO milestones 
                    (milestone_id, milestone_code, project_id, wbs_id, sow_id, milestone_name,
                     milestone_type, planned_date, actual_date, milestone_cap_amount, approval_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (milestone_id, milestone_code, project_id, wbs_id, sow_id, milestone_name,
                      milestone_type, planned_date.strftime("%Y-%m-%d"),
                      actual_date.strftime("%Y-%m-%d") if actual_date else None,
                      milestone_cap, approval_status))
                
                milestones.append({
                    "milestone_id": milestone_id,
                    "sow_id": sow_id,
                    "milestone_cap_amount": milestone_cap,
                    "planned_date": planned_date
                })
            
            milestone_global_memory_usage[sow_number] = True
        else:
            # Generate milestones randomly
            num_milestones = random.randint(3, 5)
        duration_days = (end_date - start_date).days
        milestone_interval = duration_days // (num_milestones + 1)
        
        for i in range(num_milestones):
            milestone_id = f"MIL-{uuid.uuid4().hex[:8].upper()}"
            milestone_code = f"MS-{sow_number}-{i+1:02d}"
            milestone_type = random.choice(milestone_types)
            milestone_name = f"Milestone {i+1}: {milestone_type.title()}"
            
            planned_date = start_date + timedelta(days=(i + 1) * milestone_interval)
            actual_date = planned_date + timedelta(days=random.randint(-5, 10)) if random.random() > 0.3 else None
            
            milestone_cap = round(random.uniform(50000, 200000), 2)
            approval_status = "approved" if actual_date and actual_date <= planned_date + timedelta(days=5) else "pending"
            
            wbs_id = random.choice(wbs_options)[0] if wbs_options else None
            
            cursor.execute("""
                INSERT INTO milestones 
                (milestone_id, milestone_code, project_id, wbs_id, sow_id, milestone_name,
                 milestone_type, planned_date, actual_date, milestone_cap_amount, approval_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (milestone_id, milestone_code, project_id, wbs_id, sow_id, milestone_name,
                  milestone_type, planned_date.strftime("%Y-%m-%d"),
                  actual_date.strftime("%Y-%m-%d") if actual_date else None,
                  milestone_cap, approval_status))
            
            milestones.append({
                "milestone_id": milestone_id,
                "sow_id": sow_id,
                "milestone_cap_amount": milestone_cap,
                "planned_date": planned_date
            })
    
            milestone_global_memory_usage[sow_number] = False
    
    # Count how many used global memory
    global_count = sum(1 for v in milestone_global_memory_usage.values() if v)
    if global_count > 0:
        print(f"  ✓ Generated {len(milestones)} milestones ({global_count} SOWs with milestones from global memory, {len(milestone_global_memory_usage) - global_count} generated)")
    else:
        print(f"  ✓ Generated {len(milestones)} milestones (all generated, none from global memory)")
    
    return milestones, milestone_global_memory_usage


# ============================================================================
# Policy & Controls Generation
# ============================================================================

def generate_anomaly_thresholds(cursor, vendors: List[Dict[str, Any]]) -> None:
    """Generate anomaly detection thresholds (vendor-specific with global fallback)."""
    # Global thresholds
    global_thresholds = [
        {"metric_type": "amount_spike", "baseline_value": 100000.0, "variance_percentage": 50.0, "lookback_days": 90},
        {"metric_type": "quantity_variance", "baseline_value": 100.0, "variance_percentage": 30.0, "lookback_days": 90},
        {"metric_type": "frequency_anomaly", "baseline_value": 2.0, "variance_percentage": 100.0, "lookback_days": 30}
    ]
    
    for threshold in global_thresholds:
        threshold_id = f"THRESH-GLOBAL-{threshold['metric_type'].upper()}"
        cursor.execute("""
            INSERT INTO anomaly_thresholds 
            (threshold_id, metric_type, vendor_id, baseline_value, variance_percentage, lookback_days)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (threshold_id, threshold["metric_type"], None, threshold["baseline_value"],
              threshold["variance_percentage"], threshold["lookback_days"]))
    
    # Vendor-specific thresholds (for active vendors)
    for vendor in vendors[:8]:  # Top 8 vendors get specific thresholds
        for threshold in global_thresholds:
            threshold_id = f"THRESH-{vendor['vendor_id']}-{threshold['metric_type'].upper()}"
            # Vendor-specific baselines vary by vendor
            vendor_baseline = threshold["baseline_value"] * random.uniform(0.7, 1.3)
            cursor.execute("""
                INSERT INTO anomaly_thresholds 
                (threshold_id, metric_type, vendor_id, baseline_value, variance_percentage, lookback_days)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (threshold_id, threshold["metric_type"], vendor["vendor_id"], 
                  round(vendor_baseline, 2), threshold["variance_percentage"], threshold["lookback_days"]))
    
    print(f"  ✓ Generated anomaly thresholds (global + vendor-specific)")


# ============================================================================
# Historical Data Generation (Placeholder - to be implemented)
# ============================================================================

def generate_historical_invoices(cursor, vendors: List[Dict[str, Any]], pos: List[Dict[str, Any]], 
                                 sows: List[Dict[str, Any]], count: int = 125) -> None:
    """Generate historical invoice summary data (24 months).
    
    CRITICAL FIX: Ensure historical invoices are generated for all vendor/SOW combinations
    to support anomaly detection. The anomaly validator queries by vendor_name and sow_number,
    so we need historical invoices that match these combinations.
    """
    # This generates summary data in historical_invoices table
    # Actual PDFs would be generated separately if needed
    base_date = datetime.now() - timedelta(days=730)  # 24 months ago
    
    # CRITICAL FIX: Generate at least 2-3 historical invoices per SOW to ensure anomaly detection works
    # This ensures that when current invoices are generated with abnormal_spike exception,
    # there will be historical data for the same vendor/SOW combination
    invoices_per_sow = max(2, count // max(len(sows), 1))  # At least 2 per SOW, or distribute evenly
    remaining_count = count
    
    # First, generate historical invoices for each SOW to ensure coverage
    for sow in sows:
        if remaining_count <= 0:
            break
        vendor = next((v for v in vendors if v["vendor_id"] == sow["vendor_id"]), None)
        if not vendor:
            continue
        
        # Generate 2-3 historical invoices for this SOW
        num_for_sow = min(invoices_per_sow, remaining_count)
        for i in range(num_for_sow):
            historical_id = f"HIST-{uuid.uuid4().hex[:8].upper()}"
            # Find a PO for this SOW
            po = next((p for p in pos if p.get("sow_id") == sow["sow_id"]), None)
            
            invoice_date = base_date + timedelta(days=random.randint(0, 730))
            total_amount = round(random.uniform(10000, 200000), 2)
            # Increase approved percentage to ensure payment history: 80% approved (4 out of 5)
            final_status = random.choice(["approved", "approved", "approved", "approved", "rejected"])
            
            # For approved invoices, always set payment date and amount
            # Create some late payments (30% late payment rate) to enable payment pattern anomaly detection
            if final_status == "approved":
                # 30% chance of late payment (>30 days after invoice date)
                if random.random() < 0.3:
                    # Late payment: 31-90 days after invoice date
                    payment_date = invoice_date + timedelta(days=random.randint(31, 90))
                else:
                    # On-time payment: 15-30 days after invoice date
                    payment_date = invoice_date + timedelta(days=random.randint(15, 30))
                payment_amount = round(total_amount, 2)  # Ensure it's a proper float
            else:
                payment_date = None
                payment_amount = None
            
            exceptions = [] if random.random() > 0.3 else random.sample(
                ["rate_violation", "missing_evidence", "retention_not_applied"], 
                random.randint(1, 2)
            )
            
            processing_time = round(random.uniform(2, 48), 2)
            
            # Ensure payment_amount is properly formatted
            payment_date_str = payment_date.strftime("%Y-%m-%d") if payment_date else None
            payment_amount_val = float(payment_amount) if payment_amount else None
            
            cursor.execute("""
                INSERT INTO historical_invoices 
                (historical_id, invoice_number, vendor_id, invoice_date, total_amount,
                 po_number, sow_id, final_status, payment_date, payment_amount,
                 exceptions_detected, processing_time_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (historical_id, f"HIST-INV-{remaining_count:04d}", vendor["vendor_id"],
                  invoice_date.strftime("%Y-%m-%d"), total_amount,
                  po["po_number"] if po else None, sow["sow_id"],
                  final_status, payment_date_str, payment_amount_val,
                  json.dumps(exceptions), processing_time))
            
            remaining_count -= 1
    
    # Generate remaining historical invoices randomly to reach the target count
    for i in range(remaining_count):
        historical_id = f"HIST-{uuid.uuid4().hex[:8].upper()}"
        vendor = random.choice(vendors)
        po = random.choice(pos) if pos else None
        sow = random.choice(sows) if sows else None
        
        invoice_date = base_date + timedelta(days=random.randint(0, 730))
        total_amount = round(random.uniform(10000, 200000), 2)
        # Increase approved percentage to ensure payment history: 80% approved (4 out of 5)
        final_status = random.choice(["approved", "approved", "approved", "approved", "rejected"])
        
        # For approved invoices, always set payment date and amount
        # Create some late payments (30% late payment rate) to enable payment pattern anomaly detection
        if final_status == "approved":
            # 30% chance of late payment (>30 days after invoice date)
            if random.random() < 0.3:
                # Late payment: 31-90 days after invoice date
                payment_date = invoice_date + timedelta(days=random.randint(31, 90))
            else:
                # On-time payment: 15-30 days after invoice date
                payment_date = invoice_date + timedelta(days=random.randint(15, 30))
            payment_amount = round(total_amount, 2)  # Ensure it's a proper float
        else:
            payment_date = None
            payment_amount = None
        
        exceptions = [] if random.random() > 0.3 else random.sample(
            ["rate_violation", "missing_evidence", "retention_not_applied"], 
            random.randint(1, 2)
        )
        
        processing_time = round(random.uniform(2, 48), 2)
        
        # Ensure payment_amount is properly formatted
        payment_date_str = payment_date.strftime("%Y-%m-%d") if payment_date else None
        payment_amount_val = float(payment_amount) if payment_amount else None
        
        cursor.execute("""
            INSERT INTO historical_invoices 
            (historical_id, invoice_number, vendor_id, invoice_date, total_amount,
             po_number, sow_id, final_status, payment_date, payment_amount,
             exceptions_detected, processing_time_hours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (historical_id, f"HIST-INV-{i+1:04d}", vendor["vendor_id"],
              invoice_date.strftime("%Y-%m-%d"), total_amount,
              po["po_number"] if po else None, sow["sow_id"] if sow else None,
              final_status, payment_date_str, payment_amount_val,
              json.dumps(exceptions), processing_time))
    
    print(f"  ✓ Generated {count} historical invoice records")
    
    # Populate payment_history from approved invoices
    # Note: This must be called before commit to ensure payment_history is populated
    populate_payment_history(cursor)


def populate_payment_history(cursor) -> None:
    """Populate payment_history table from historical_invoices that were paid.
    
    Purpose: The payment_history table tracks actual payment transactions separately
    from invoice data. This is used by the Historical Pattern & Anomaly Agent to:
    - Analyze payment behavior patterns (on-time vs late payments)
    - Detect payment anomalies (unusual payment amounts, frequencies)
    - Build vendor payment reliability baselines
    - Flag vendors with payment history issues
    """
    # First, check how many approved invoices we have
    cursor.execute("""
        SELECT COUNT(*) FROM historical_invoices
        WHERE final_status = 'approved' 
          AND payment_date IS NOT NULL 
          AND payment_amount IS NOT NULL
          AND vendor_id IS NOT NULL
    """)
    approved_count = cursor.fetchone()[0]
    
    if approved_count == 0:
        print(f"  ⚠ Warning: No approved invoices with payment data found in historical_invoices.")
        print(f"     This might indicate an issue with historical invoice generation.")
        return
    
    # Query historical invoices that were approved and have payment dates
    cursor.execute("""
        SELECT invoice_number, vendor_id, po_number, payment_date, payment_amount
        FROM historical_invoices
        WHERE final_status = 'approved' 
          AND payment_date IS NOT NULL 
          AND payment_amount IS NOT NULL
          AND vendor_id IS NOT NULL
    """)
    
    paid_invoices = cursor.fetchall()
    payment_methods = ["ACH", "Wire Transfer", "Check", "Credit Card", "Bank Transfer"]
    
    payment_count = 0
    error_count = 0
    
    for row in paid_invoices:
        invoice_number, vendor_id, po_number, payment_date, payment_amount = row
        
        # Skip if essential fields are missing
        if not vendor_id or not payment_date or not payment_amount:
            continue
        
        payment_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        
        # Determine payment status (most are completed, some might be pending/partial)
        if random.random() > 0.95:  # 5% chance of non-completed
            payment_status = random.choice(["pending", "partial", "failed"])
            # Adjust amount for partial payments
            if payment_status == "partial":
                payment_amount = round(float(payment_amount) * random.uniform(0.5, 0.9), 2)
        else:
            payment_status = "completed"
        
        payment_method = random.choice(payment_methods)
        
        try:
            cursor.execute("""
                INSERT INTO payment_history 
                (payment_id, invoice_id, po_number, vendor_id, payment_date, 
                 payment_amount, payment_status, payment_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (payment_id, invoice_number, po_number, vendor_id, payment_date,
                  float(payment_amount), payment_status, payment_method))
            payment_count += 1
        except Exception as e:
            # Log error but continue with other records
            error_count += 1
            if error_count <= 3:  # Only show first 3 errors to avoid spam
                print(f"  ⚠ Warning: Failed to insert payment record for {invoice_number}: {e}")
            continue
    
    if payment_count == 0:
        print(f"  ⚠ Warning: No payment history records were created.")
        print(f"     Found {approved_count} approved invoices but failed to create payment records.")
        if error_count > 0:
            print(f"     {error_count} errors occurred during insertion.")
    else:
        print(f"  ✓ Populated {payment_count} payment history records from {approved_count} approved invoices")


# ============================================================================
# PDF Generation Functions
# ============================================================================

def format_currency(amount: float) -> str:
    """Format currency amount as GBP with comma separators."""
    return f"£{amount:,.2f}"


def generate_signature_text(name: str) -> str:
    """Generate a realistic signature text from a name."""
    # Create signature-like text (e.g., "John Smith" -> "J. Smith" or "John S.")
    parts = name.split()
    if len(parts) >= 2:
        # Format: "J. Smith" or "John S."
        if random.random() > 0.5:
            return f"{parts[0][0]}. {parts[-1]}"
        else:
            return f"{parts[0]} {parts[-1][0]}."
    return name


def get_evidence_format_style(invoice_number: str) -> str:
    """Get format style for evidence documents based on invoice number (for variation)."""
    # Use invoice number hash to determine format style
    hash_val = hash(invoice_number) % 4
    styles = ["standard", "compact", "detailed", "minimal"]
    return styles[hash_val]


def get_invoice_format_variation(invoice_number: str) -> str:
    """Get format variation for invoice based on invoice number (for more variety)."""
    hash_val = hash(invoice_number) % 6
    variations = ["standard", "compact", "detailed", "minimal", "spacious", "condensed"]
    return variations[hash_val]


def get_vendor_branding(vendor_name: str) -> Dict[str, Any]:
    """Get vendor-specific branding (colors, layout style, etc.)."""
    # Vendor-specific color schemes and styles
    branding_map = {
        "Offshore Drilling Services Inc": {
            "primary_color": "#003366",  # Deep blue
            "secondary_color": "#0066CC",
            "accent_color": "#FF6600",
            "layout_style": "modern",
            "logo_text": "ODS"
        },
        "PetroLogistics Solutions": {
            "primary_color": "#1B4332",  # Dark green
            "secondary_color": "#40916C",
            "accent_color": "#D4AF37",
            "layout_style": "classic",
            "logo_text": "PLS"
        },
        "Marine Engineering Corp": {
            "primary_color": "#0D47A1",  # Navy blue
            "secondary_color": "#1976D2",
            "accent_color": "#FFC107",
            "layout_style": "professional",
            "logo_text": "MEC"
        },
        "Rig Maintenance Specialists": {
            "primary_color": "#B71C1C",  # Red
            "secondary_color": "#E53935",
            "accent_color": "#FFD700",
            "layout_style": "industrial",
            "logo_text": "RMS"
        },
        "Pipeline Construction Group": {
            "primary_color": "#1A237E",  # Indigo
            "secondary_color": "#3F51B5",
            "accent_color": "#00BCD4",
            "layout_style": "modern",
            "logo_text": "PCG"
        },
        "Well Completion Services": {
            "primary_color": "#004D40",  # Teal
            "secondary_color": "#00796B",
            "accent_color": "#FF6F00",
            "layout_style": "classic",
            "logo_text": "WCS"
        },
        "Subsea Equipment Suppliers": {
            "primary_color": "#212121",  # Dark grey
            "secondary_color": "#424242",
            "accent_color": "#00E676",
            "layout_style": "professional",
            "logo_text": "SES"
        },
        "Vessel Operations Ltd": {
            "primary_color": "#01579B",  # Light blue
            "secondary_color": "#0277BD",
            "accent_color": "#FF9800",
            "layout_style": "maritime",
            "logo_text": "VOL"
        },
        "Safety & Compliance Partners": {
            "primary_color": "#1B5E20",  # Green
            "secondary_color": "#388E3C",
            "accent_color": "#FFD700",
            "layout_style": "professional",
            "logo_text": "SCP"
        },
        "Environmental Services Co": {
            "primary_color": "#2E7D32",  # Forest green
            "secondary_color": "#4CAF50",
            "accent_color": "#FFC107",
            "layout_style": "eco",
            "logo_text": "ESC"
        },
        "Equipment Rental Solutions": {
            "primary_color": "#5D4037",  # Brown
            "secondary_color": "#795548",
            "accent_color": "#FF5722",
            "layout_style": "industrial",
            "logo_text": "ERS"
        },
        "Technical Consulting Group": {
            "primary_color": "#311B92",  # Purple
            "secondary_color": "#512DA8",
            "accent_color": "#00BCD4",
            "layout_style": "modern",
            "logo_text": "TCG"
        }
    }
    
    # Default branding if vendor not found - use initials from vendor name
    default_logo = "".join([word[0].upper() for word in vendor_name.split()[:3]])[:4]  # First 3-4 letters max
    if not default_logo:
        default_logo = "VND"
    
    default_branding = {
        "primary_color": "#1a5490",
        "secondary_color": "#4A90E2",
        "accent_color": "#FF6B35",
        "layout_style": "professional",
        "logo_text": default_logo
    }
    
    return branding_map.get(vendor_name, default_branding)


def create_logo_placeholder(branding: Dict[str, Any], width: float = 2 * inch, height: float = 0.75 * inch) -> Table:
    """Create a professional logo placeholder with company branding."""
    from reportlab.platypus import Image
    
    # Create a styled table that looks like a logo
    logo_data = [[branding["logo_text"]]]
    logo_table = Table(logo_data, colWidths=[width], rowHeights=[height])
    
    logo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(branding["primary_color"])),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 24),
        ('LINEBELOW', (0, 0), (-1, -1), 2, colors.HexColor(branding["accent_color"])),
    ]))
    
    return logo_table


def generate_invoice_pdf(output_dir: Path, invoice_data: Dict[str, Any], exception_scenario: Optional[Dict[str, Any]] = None, language: str = "en") -> str:
    """Generate a professional invoice PDF with vendor branding in specified language.
    
    Args:
        output_dir: Directory to save PDF
        invoice_data: Invoice data dictionary
        exception_scenario: Optional exception scenario data
        language: ISO 639-1 language code (default: 'en')
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is required for PDF generation")
    
    filename = f"{invoice_data['invoice_number']}.pdf"
    filepath = output_dir / filename
    
    # Get language templates
    templates = get_language_template(language)
    font_name = get_font_for_language(language)
    
    vendor_name = invoice_data['vendor_name']
    branding = get_vendor_branding(vendor_name)
    layout_style = branding["layout_style"]
    format_variation = get_invoice_format_variation(invoice_data['invoice_number'])
    
    # Calculate available width: Letter (8.5") - margins (0.75" each side) = 7"
    available_width = 7 * inch
    doc = SimpleDocTemplate(str(filepath), pagesize=letter,
                           leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                           topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Vendor-specific custom styles
    header_style = ParagraphStyle(
        'VendorHeader',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor(branding["primary_color"]),
        spaceAfter=6,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    invoice_title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor(branding["primary_color"]),
        spaceAfter=12,
        alignment=TA_RIGHT,
        fontName='Helvetica-Bold'
    )
    
    # Header section with logo and company info
    header_data = []
    
    if layout_style in ["modern", "professional"]:
        # Two-column header: Logo + Company info left, Invoice title right
        # Use smaller logo to prevent overlap
        logo_table = create_logo_placeholder(branding, width=2.0 * inch, height=0.5 * inch)
        
        # Company info with proper styling - use smaller font to prevent overflow
        company_style = ParagraphStyle(
            'CompanyInfo',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.black,
            spaceAfter=1,
            leading=10,
            fontName=font_name
        )
        
        # Create left column as a table cell with all content
        left_col_table = Table([
            [[logo_table]],
            [[Paragraph(vendor_name, ParagraphStyle('VendorName', parent=header_style, fontSize=16, fontName=font_name))]],
            [[Paragraph("Oil & Gas Services", company_style)]],
            [[Paragraph("123 Industry Blvd, Houston, TX 77001", company_style)]],
            [[Paragraph(f"{templates['phone']} (713) 555-0100 | {templates['email']} info@vendor.com", company_style)]]
        ], colWidths=[4.0 * inch])
        left_col_table.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        # Right side: Invoice title (smaller to fit)
        invoice_title_cell = Paragraph(templates["invoice"].upper(), ParagraphStyle('InvoiceTitleRight', parent=invoice_title_style, fontSize=24, fontName=font_name))
        
        # Create header table - simpler structure
        header_table = Table([
            [left_col_table, invoice_title_cell]
        ], colWidths=[4.2 * inch, 2.3 * inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)
        
    elif layout_style == "classic":
        # Centered header with logo, company name, and invoice title
        logo_table = create_logo_placeholder(branding, width=3.5 * inch, height=0.8 * inch)
        
        # Center everything
        centered_header = Table([
            [logo_table],
            [Paragraph(vendor_name, ParagraphStyle('CenteredHeader', parent=header_style, alignment=TA_CENTER, fontName=font_name))],
            [Paragraph(templates["invoice"].upper(), ParagraphStyle('CenteredTitle', parent=invoice_title_style, alignment=TA_CENTER, fontSize=24, fontName=font_name))],
            [Paragraph("Oil & Gas Services", ParagraphStyle('CenteredSub', parent=styles['Normal'], alignment=TA_CENTER, fontSize=9, fontName=font_name))]
        ], colWidths=[available_width])
        centered_header.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(centered_header)
        
    elif layout_style in ["industrial", "maritime"]:
        # Full-width colored header bar with logo and text - simplified to prevent overlap
        header_style_white = ParagraphStyle(
            'HeaderWhite',
            parent=header_style,
            textColor=colors.whitesmoke,
            fontSize=16,
            alignment=TA_CENTER
        )
        invoice_title_white = ParagraphStyle(
            'TitleWhite',
            parent=invoice_title_style,
            textColor=colors.whitesmoke,
            fontSize=20,
            alignment=TA_CENTER
        )
        
        # Create header with logo on left, text in center/right - simpler structure
        logo_small = create_logo_placeholder(branding, width=1.2 * inch, height=0.6 * inch)
        
        # Text content as table cells
        text_table = Table([
            [[Paragraph(vendor_name, ParagraphStyle('HeaderWhiteVendor', parent=header_style_white, fontName=font_name))]],
            [[Paragraph(templates["invoice"].upper(), ParagraphStyle('InvoiceTitleWhite', parent=invoice_title_white, fontName=font_name))]],
            [[Paragraph("Oil & Gas Services", ParagraphStyle('SubWhite', parent=styles['Normal'], 
                textColor=colors.whitesmoke, fontSize=7, alignment=TA_CENTER, fontName=font_name))]]
        ], colWidths=[4.5 * inch])
        text_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        header_content = Table([
            [logo_small, text_table]
        ], colWidths=[1.4 * inch, 4.9 * inch])
        header_content.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(branding["primary_color"])),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(header_content)
        
    else:  # eco or default
        # Clean header with logo, company info, and colored accent bar - simplified
        logo_compact = create_logo_placeholder(branding, width=1.8 * inch, height=0.5 * inch)
        
        # Text content as table
        text_table_eco = Table([
            [[Paragraph(vendor_name, ParagraphStyle('EcoVendor', parent=header_style, fontSize=16, fontName=font_name))]],
            [[Paragraph(templates["invoice"].upper(), ParagraphStyle('EcoTitle', parent=invoice_title_style, fontSize=20, fontName=font_name))]],
            [[Paragraph("Oil & Gas Services", ParagraphStyle('EcoSub', parent=styles['Normal'], fontSize=8, fontName=font_name))]]
        ], colWidths=[4.3 * inch])
        text_table_eco.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        header_eco = Table([
            [logo_compact, text_table_eco]
        ], colWidths=[1.9 * inch, 4.4 * inch])
        header_eco.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(header_eco)
        
        # Add colored accent line below
        line = Table([[""]], colWidths=[available_width], rowHeights=[0.08 * inch])
        line.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(branding["accent_color"])),
        ]))
        story.append(line)
    
    story.append(Spacer(1, 0.2 * inch))
    
    # Invoice details section with branded styling
    details_heading_style = ParagraphStyle(
        'DetailsHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor(branding["primary_color"]),
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    
    if layout_style in ["modern", "professional"]:
        # Create style for invoice detail labels to support CJK fonts
        detail_label_style = ParagraphStyle(
            'DetailLabel',
            parent=styles['Normal'],
            fontSize=9,
            fontName=font_name
        )
        
        # Create style for invoice detail values to support CJK fonts
        detail_value_style = ParagraphStyle(
            'DetailValue',
            parent=styles['Normal'],
            fontSize=9,
            fontName=font_name
        )
        
        # Two-column layout: Invoice details left, Bill To right
        invoice_details_data = [
            [Paragraph(f"{templates['invoice_number']}:", detail_label_style), Paragraph(str(invoice_data['invoice_number']), detail_value_style)],
            [Paragraph(f"{templates['invoice_date']}:", detail_label_style), Paragraph(str(invoice_data['invoice_date']), detail_value_style)],
            [Paragraph(f"{templates['due_date']}:", detail_label_style), Paragraph(str(invoice_data['due_date']), detail_value_style)],
            [Paragraph(f"{templates['po_reference']}:", detail_label_style), Paragraph(str(invoice_data.get('po_reference', 'N/A')), detail_value_style)],
            [Paragraph(f"{templates['sow_reference']}:", detail_label_style), Paragraph(str(invoice_data.get('sow_reference', 'N/A')), detail_value_style)],
            [Paragraph(f"{templates['project_reference']}:", detail_label_style), Paragraph(str(invoice_data.get('project_reference', 'N/A')), detail_value_style)],
            [Paragraph(f"{templates['wbs_reference']}:", detail_label_style), Paragraph(str(invoice_data.get('wbs_reference', 'N/A')), detail_value_style)],
        ]
        
        # Add multi-project info if applicable
        if invoice_data.get('additional_projects'):
            for idx, proj in enumerate(invoice_data['additional_projects'], 1):
                invoice_details_data.append([
                    Paragraph(f"{templates['project_reference']} {idx}:", detail_label_style),
                    Paragraph(f"{proj.get('project_code', 'N/A')} / {proj.get('wbs_code', 'N/A')}", detail_value_style)
                ])
        
        # Build Bill To data to match invoice details row count
        bill_to_data = [
            [Paragraph(templates['bill_to'], detail_label_style), Paragraph("Oil & Gas Company Inc", detail_value_style)],
            [Paragraph("", detail_label_style), Paragraph("123 Energy Drive", detail_value_style)],
            [Paragraph("", detail_label_style), Paragraph("Houston, TX 77002", detail_value_style)],
        ]
        
        # Calculate how many more rows we need to match invoice_details
        invoice_row_count = len(invoice_details_data)
        bill_to_row_count = len(bill_to_data)
        
        # Add empty rows to match invoice details, then add Payment Terms at the end
        rows_needed = invoice_row_count - bill_to_row_count - 1  # -1 for Payment Terms row
        for _ in range(max(0, rows_needed)):
            bill_to_data.append([Paragraph("", detail_label_style), Paragraph("", detail_value_style)])
        
        # Add Payment Terms as the last row
        bill_to_data.append([Paragraph(templates['payment_terms'] + ":", detail_label_style), Paragraph("Net 30", detail_value_style)])
        
        # Ensure both tables have the same number of rows
        while len(bill_to_data) < len(invoice_details_data):
            bill_to_data.append([Paragraph("", detail_label_style), Paragraph("", detail_value_style)])
        while len(invoice_details_data) < len(bill_to_data):
            invoice_details_data.append([Paragraph("", detail_label_style), Paragraph("", detail_value_style)])
        
        # Create inner tables with styling
        # Key: Outer table column widths must be >= inner table total width to prevent overflow
        # Strategy: Reduce inner table widths so they fit in smaller outer columns, leaving right margin
        # Inner tables: 1.5" + 2.5" = 4.0" each
        # Outer table: 3.2" + 3.2" = 6.4" total (fits in 7" available width with 0.6" right margin)
        invoice_table = Table(invoice_details_data, colWidths=[1.5 * inch, 2.5 * inch])
        invoice_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            # Font is set via Paragraph objects above, so no need for FONTNAME here
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            # Horizontal lines between rows (blue)
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor(branding["primary_color"])),
            ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.HexColor(branding["secondary_color"])),
            # No vertical lines - clean look
        ]))
        
        bill_table = Table(bill_to_data, colWidths=[1.5 * inch, 2.5 * inch])
        bill_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            # Font is set via Paragraph objects above, so no need for FONTNAME here
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            # Horizontal lines between rows (blue)
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor(branding["primary_color"])),
            ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.HexColor(branding["secondary_color"])),
            # No vertical lines - clean look
        ]))
        
        # Outer table: 3.2" + 3.2" = 6.4" total
        # Inner tables are 4.0" each (1.5" + 2.5"), so they fit comfortably in 3.2" outer columns
        # This leaves 0.6" margin on the right side (7" available - 6.4" table = 0.6")
        details_table = Table([
            [invoice_table, bill_table]
        ], colWidths=[3.2 * inch, 3.2 * inch])
        
        details_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        # Wrap in a centered container table to center-align on the page
        # Left spacer + table + right spacer = available width
        table_width = 6.4 * inch
        left_spacer = (available_width - table_width) / 2
        centered_table = Table([
            [Spacer(1, left_spacer), details_table]
        ], colWidths=[left_spacer, table_width])
        
        centered_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        # Use the centered table instead
        details_table = centered_table
        
    else:
        # Single column layout
        # Create style for invoice detail labels to support CJK fonts
        detail_label_style = ParagraphStyle(
            'DetailLabel',
            parent=styles['Normal'],
            fontSize=9,
            fontName=font_name
        )
        
        # Create style for invoice detail values to support CJK fonts
        detail_value_style = ParagraphStyle(
            'DetailValue',
            parent=styles['Normal'],
            fontSize=9,
            fontName=font_name
        )
        
        invoice_details_data = [
            [Paragraph(f"{templates['invoice_number']}:", detail_label_style), Paragraph(str(invoice_data['invoice_number']), detail_value_style)],
            [Paragraph(f"{templates['invoice_date']}:", detail_label_style), Paragraph(str(invoice_data['invoice_date']), detail_value_style)],
            [Paragraph(f"{templates['due_date']}:", detail_label_style), Paragraph(str(invoice_data['due_date']), detail_value_style)],
            [Paragraph(f"{templates['po_reference']}:", detail_label_style), Paragraph(str(invoice_data.get('po_reference', 'N/A')), detail_value_style)],
            [Paragraph(f"{templates['sow_reference']}:", detail_label_style), Paragraph(str(invoice_data.get('sow_reference', 'N/A')), detail_value_style)],
            [Paragraph(f"{templates['project_reference']}:", detail_label_style), Paragraph(str(invoice_data.get('project_reference', 'N/A')), detail_value_style)],
            [Paragraph(f"{templates['wbs_reference']}:", detail_label_style), Paragraph(str(invoice_data.get('wbs_reference', 'N/A')), detail_value_style)],
        ]
        
        if invoice_data.get('additional_projects'):
            for idx, proj in enumerate(invoice_data['additional_projects'], 1):
                invoice_details_data.append([
                    Paragraph(f"{templates['project_reference']} {idx}:", detail_label_style),
                    Paragraph(f"{proj.get('project_code', 'N/A')} / {proj.get('wbs_code', 'N/A')}", detail_value_style)
                ])
        
        # Single column: 1.8" + 4.9" = 6.7" (fits in 7" with margin)
        details_table = Table(invoice_details_data, colWidths=[1.8 * inch, 4.9 * inch])
        details_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            # Font is set via Paragraph objects above, so no need for FONTNAME here
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(branding["secondary_color"])),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(branding["primary_color"])),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ]))
    
    story.append(details_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Line items with branded header
    story.append(Paragraph(templates['line_items'], ParagraphStyle('LineItemsHeading', parent=details_heading_style, fontName=font_name)))
    # Line item headers - use abbreviated forms for table headers
    # Convert header cells to Paragraph objects with proper font for CJK support
    qty_label = templates['quantity'][:3] if len(templates['quantity']) > 3 else templates['quantity']
    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=9,
        fontName=font_name,
        textColor=colors.whitesmoke
    )
    # Add PO Line Reference column if any line items have it
    has_po_line_ref = any(item.get('po_line_number') for item in invoice_data['line_items'])
    
    if has_po_line_ref:
        line_item_data = [[
            Paragraph(templates['item_code'], header_style),
            Paragraph(templates.get('po_line_reference', 'PO Line'), header_style),
            Paragraph(templates['description'], header_style),
            Paragraph(qty_label, header_style),
            Paragraph(templates['unit_price'], header_style),
            Paragraph(templates['total'], header_style)
        ]]
    else:
        line_item_data = [[
            Paragraph(templates['item_code'], header_style),
            Paragraph(templates['description'], header_style),
            Paragraph(qty_label, header_style),
            Paragraph(templates['unit_price'], header_style),
            Paragraph(templates['total'], header_style)
        ]]
    
    # Create style for line item values to support CJK fonts
    line_item_value_style = ParagraphStyle(
        'LineItemValue',
        parent=styles['Normal'],
        fontSize=8,
        fontName=font_name
    )
    
    for item in invoice_data['line_items']:
        # Debug: Print what we're reading from line_items
        print(f"  [DEBUG] PDF generation: Reading item quantity={item.get('quantity')}, unit_price={item.get('unit_price')}, total={item.get('total')}")
        # Wrap description text to prevent overflow
        description_text = item['description']
        # Use same font size as other line item values
        description_para = Paragraph(description_text, ParagraphStyle('DescriptionLang', parent=line_item_value_style, fontName=font_name))
        
        if has_po_line_ref:
            # Include PO line reference
            po_line_ref = f"{item.get('po_reference', '')}-{item.get('po_line_number', 'N/A')}" if item.get('po_line_number') else ""
            line_item_data.append([
                Paragraph(str(item.get('item_code', '')), line_item_value_style),
                Paragraph(po_line_ref, line_item_value_style),
                description_para,
                Paragraph(str(item['quantity']), line_item_value_style),
                Paragraph(format_currency(item['unit_price']), line_item_value_style),
                Paragraph(format_currency(item['total']), line_item_value_style),
            ])
        else:
            line_item_data.append([
                Paragraph(str(item.get('item_code', '')), line_item_value_style),
                description_para,
                Paragraph(str(item['quantity']), line_item_value_style),
                Paragraph(format_currency(item['unit_price']), line_item_value_style),
                Paragraph(format_currency(item['total']), line_item_value_style),
            ])
    
    # Line items table: adjust based on format variation and whether PO line ref is included
    if has_po_line_ref:
        if format_variation in ["compact", "condensed"]:
            # Compact with PO line: 0.8" + 1.0" + 1.5" + 0.6" + 1.0" + 0.9" = 5.8"
            item_table = Table(line_item_data, colWidths=[0.8 * inch, 1.0 * inch, 1.5 * inch, 0.6 * inch, 1.0 * inch, 0.9 * inch])
        elif format_variation == "spacious":
            # Spacious with PO line: 1.0" + 1.2" + 2.0" + 0.8" + 1.2" + 1.1" = 7.3" (slightly over, will wrap)
            item_table = Table(line_item_data, colWidths=[1.0 * inch, 1.2 * inch, 2.0 * inch, 0.8 * inch, 1.2 * inch, 1.1 * inch])
        else:
            # Standard with PO line: 0.9" + 1.0" + 1.8" + 0.7" + 1.1" + 1.0" = 6.5" (fits in 7")
            item_table = Table(line_item_data, colWidths=[0.9 * inch, 1.0 * inch, 1.8 * inch, 0.7 * inch, 1.1 * inch, 1.0 * inch])
    else:
        if format_variation in ["compact", "condensed"]:
            # Compact: 0.8" + 2.1" + 0.6" + 1.0" + 0.9" = 5.4"
            item_table = Table(line_item_data, colWidths=[0.8 * inch, 2.1 * inch, 0.6 * inch, 1.0 * inch, 0.9 * inch])
        elif format_variation == "spacious":
            # Spacious: 1.0" + 2.5" + 0.8" + 1.2" + 1.1" = 6.6"
            item_table = Table(line_item_data, colWidths=[1.0 * inch, 2.5 * inch, 0.8 * inch, 1.2 * inch, 1.1 * inch])
        else:
            # Standard: 0.9" + 2.3" + 0.7" + 1.1" + 1.0" = 6.0" (fits in 7")
            item_table = Table(line_item_data, colWidths=[0.9 * inch, 2.3 * inch, 0.7 * inch, 1.1 * inch, 1.0 * inch])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(branding["primary_color"])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        # Header row font is set via Paragraph objects above, so no need for FONTNAME here
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
    ]))
    story.append(item_table)
    story.append(Spacer(1, 0.25 * inch))
    
    # Totals
    subtotal = invoice_data['total_amount']
    tax_amount = invoice_data.get('tax_amount', 0)
    
    # Apply retention if applicable (exception: retention_not_applied means it's missing)
    retention_applied = invoice_data.get('retention_applied', True)
    retention_amount = 0
    if invoice_data.get('retention_percentage') and retention_applied:
        retention_amount = round(subtotal * (invoice_data['retention_percentage'] / 100), 2)
    
    # Apply LD if applicable (exception: ld_not_applied means it's missing)
    ld_amount = 0
    if invoice_data.get('ld_applicable') and invoice_data.get('ld_amount') and invoice_data.get('ld_applied', True):
        ld_amount = invoice_data['ld_amount']
    
    # Totals section with branded styling
    # Create Paragraph objects for totals labels to support CJK fonts
    totals_label_style = ParagraphStyle(
        'TotalsLabel',
        parent=styles['Normal'],
        fontSize=10,
        fontName=font_name
    )
    
    # Create style for totals values to support CJK fonts
    totals_value_style = ParagraphStyle(
        'TotalsValue',
        parent=styles['Normal'],
        fontSize=10,
        fontName=font_name
    )
    
    total_data = [
        [Paragraph(f"{templates['subtotal']}:", totals_label_style), Paragraph(format_currency(subtotal), totals_value_style)],
    ]
    
    if tax_amount > 0:
        total_data.append([Paragraph(f"{templates['tax']}:", totals_label_style), Paragraph(format_currency(tax_amount), totals_value_style)])
    
    if retention_amount > 0:
        total_data.append([Paragraph(f"{templates['retention']} ({invoice_data.get('retention_percentage', 0)}%):", totals_label_style), Paragraph(f"-{format_currency(retention_amount)}", totals_value_style)])
    
    if ld_amount > 0:
        total_data.append([Paragraph(f"{templates['liquidated_damages']}:", totals_label_style), Paragraph(f"-{format_currency(ld_amount)}", totals_value_style)])
    
    net_total = subtotal + tax_amount - retention_amount - ld_amount
    total_data.append([Paragraph(f"{templates['total_amount']}:", totals_label_style), Paragraph(format_currency(net_total), totals_value_style)])
    
    # Totals table: adjust based on format variation
    if format_variation in ["compact", "condensed"]:
        # Compact: 4.8" + 1.4" = 6.2"
        total_table = Table(total_data, colWidths=[4.8 * inch, 1.4 * inch])
    elif format_variation == "spacious":
        # Spacious: 5.2" + 1.6" = 6.8"
        total_table = Table(total_data, colWidths=[5.2 * inch, 1.6 * inch])
    else:
        # Standard: 5.0" + 1.5" = 6.5" (fits in 7")
        total_table = Table(total_data, colWidths=[5.0 * inch, 1.5 * inch])
    total_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        # Font for labels is set via Paragraph objects above
        # Only set font for the total amount (last row, right column)
        ('FONTNAME', (-1, -1), (-1, -1), font_name),  # Use font_name for CJK support
        ('FONTSIZE', (0, 0), (-1, -2), 10),
        ('FONTSIZE', (-1, -1), (-1, -1), 14),
        ('TEXTCOLOR', (-1, -1), (-1, -1), colors.HexColor(branding["primary_color"])),
        ('LINEABOVE', (-1, -1), (-1, -1), 2, colors.HexColor(branding["accent_color"])),
        ('LINEBELOW', (0, -2), (-1, -2), 1, colors.grey),
        ('BACKGROUND', (-1, -1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('TOPPADDING', (-1, -1), (-1, -1), 8),
        ('BOTTOMPADDING', (-1, -1), (-1, -1), 8),
    ]))
    story.append(total_table)
    
    # Add evidence references if applicable
    if invoice_data.get('evidence_references'):
        story.append(Spacer(1, 0.3 * inch))
        evid_heading = ParagraphStyle(
            'EvidenceHeading',
            parent=styles['Heading3'],
            fontSize=10,
            textColor=colors.HexColor(branding["primary_color"]),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph(f"{templates['evidence_references']}:", ParagraphStyle('EvidenceHeadingLang', parent=evid_heading, fontName=font_name)))
        evid_ref_style = ParagraphStyle(
            'EvidenceRef',
            parent=styles['Normal'],
            fontSize=9,
            fontName=font_name
        )
        for evid_ref in invoice_data['evidence_references']:
            story.append(Paragraph(f"• {evid_ref}", evid_ref_style))
    
    # Footer with payment terms and contact info
    story.append(Spacer(1, 0.4 * inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceBefore=10,
        fontName=font_name
    )
    
    footer_line = Table([[""]], colWidths=[available_width], rowHeights=[0.02 * inch])
    footer_line.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(branding["secondary_color"])),
    ]))
    story.append(footer_line)
    
    footer_text = (
        f"{templates['payment_terms_text']} | "
        f"{templates['questions']} {templates['contact_us']} | "
        f"{templates['thank_you']}"
    )
    story.append(Paragraph(footer_text, footer_style))
    
    # Add handwritten notes for OCR challenge (randomly)
    if random.random() > 0.7:
        story.append(Spacer(1, 0.2 * inch))
        note_style = ParagraphStyle(
            'HandwrittenNote',
            parent=styles['Normal'],
            fontSize=9,
            fontName=font_name,  # Use CJK font for Mandarin support
            textColor=colors.HexColor('#666666'),
            leftIndent=20,
            borderPadding=5,
            backColor=colors.HexColor('#FFF9E6')
        )
        story.append(Paragraph(templates['note_process_payment'], note_style))
    
    doc.build(story)
    return str(filepath)


def _get_evidence_references_for_invoice_type(invoice_type: str, invoice_number: str) -> List[str]:
    """Get evidence references based on invoice type."""
    evidence_map = {
        "LABOR": [f"Timesheet-{invoice_number}"],
        "MATERIAL": [f"GRN-{invoice_number}"],
        "PROFORMA": [f"Timesheet-{invoice_number}", f"Completion-Cert-{invoice_number}", f"GRN-{invoice_number}"]
    }
    return evidence_map.get(invoice_type, [f"Timesheet-{invoice_number}", f"Completion-Cert-{invoice_number}", f"GRN-{invoice_number}"])


def _generate_line_item_description(invoice_type: str, item_code: str, role: Optional[str] = None, 
                                     material_category: Optional[str] = None, line_num: int = 1) -> str:
    """Generate intelligent line item descriptions based on invoice type and project activities."""
    
    if invoice_type == "LABOR":
        # Labor activities for oil & gas projects
        labor_activities = [
            "Engineering Design & Analysis",
            "Project Management & Coordination",
            "Field Installation & Commissioning",
            "Quality Assurance & Inspection",
            "Safety & Environmental Compliance",
            "Technical Documentation & Reporting",
            "Equipment Testing & Validation",
            "Process Optimization & Troubleshooting",
            "Training & Knowledge Transfer",
            "Site Survey & Assessment",
            "System Integration & Configuration",
            "Maintenance & Support Services"
        ]
        activity = random.choice(labor_activities)
        if role:
            return f"{role} - {activity}"
        else:
            hours = random.randint(40, 160)
            return f"{activity} - {hours} hours"
    
    elif invoice_type == "MATERIAL":
        # Material descriptions for oil & gas projects
        material_descriptions = {
            "Steel": [
                "Carbon Steel Pipe Schedule 40",
                "Stainless Steel Flange ASME B16.5",
                "Structural Steel Beams & Plates",
                "Steel Pipe Fittings & Elbows",
                "Steel Gaskets & Bolting Kits"
            ],
            "Valves": [
                "Gate Valve - ANSI Class 150",
                "Ball Valve - Full Port Design",
                "Control Valve with Actuator",
                "Check Valve - Swing Type",
                "Pressure Relief Valve Set"
            ],
            "Piping": [
                "Process Piping Installation",
                "Pipe Supports & Hangers",
                "Pipe Insulation & Cladding",
                "Welding Consumables & Electrodes",
                "Pipe Fittings & Reducers"
            ],
            "Electrical": [
                "Motor Control Center (MCC)",
                "Power Distribution Panel",
                "Instrumentation Cables & Wiring",
                "Lighting Fixtures & Controls",
                "Electrical Conduit & Fittings"
            ],
            "Instrumentation": [
                "Pressure Transmitter & Gauge",
                "Flow Meter - Ultrasonic Type",
                "Temperature Sensor & Controller",
                "Level Measurement System",
                "Control System Components"
            ],
            "Civil": [
                "Concrete Foundation & Structures",
                "Reinforcing Steel Bars",
                "Structural Steel Framework",
                "Site Preparation & Earthworks",
                "Drainage & Utilities"
            ]
        }
        
        if material_category and material_category in material_descriptions:
            descriptions = material_descriptions[material_category]
        else:
            # Flatten all descriptions if category not found
            descriptions = [desc for cat_descs in material_descriptions.values() for desc in cat_descs]
        
        return random.choice(descriptions)
    
    else:  # PROFORMA - mix of labor and material
        # Proforma can have both types - determine based on role, material_category, or item_code prefix
        is_labor = False
        if role:  # If role is present, it's labor
            is_labor = True
        elif item_code.startswith("LAB-"):
            is_labor = True
        elif material_category:  # If material_category is present, it's material
            is_labor = False
        elif item_code.startswith("MAT-"):
            is_labor = False
        else:
            # Randomly assign if unclear (50/50 split for variety)
            is_labor = random.random() < 0.5
        
        if is_labor:
            labor_activities = [
                "Engineering & Design Services",
                "Project Management & Coordination",
                "Installation & Commissioning",
                "Quality Control & Inspection",
                "Technical Support & Training",
                "Field Engineering & Supervision",
                "System Integration & Testing",
                "Documentation & Reporting",
                "Safety & Compliance Services",
                "Equipment Calibration & Maintenance"
            ]
            activity = random.choice(labor_activities)
            if role:
                return f"{role} - {activity}"
            else:
                hours = random.randint(40, 160)
                return f"{activity} - {hours} hours"
        else:
            # Material items - use material_category if available for more specific descriptions
            if material_category:
                material_descriptions = {
                    "Steel": [
                        "Carbon Steel Pipe Schedule 40",
                        "Stainless Steel Flange ASME B16.5",
                        "Structural Steel Beams & Plates"
                    ],
                    "Valves": [
                        "Gate Valve - ANSI Class 150",
                        "Ball Valve - Full Port Design",
                        "Control Valve with Actuator"
                    ],
                    "Piping": [
                        "Process Piping Installation",
                        "Pipe Supports & Hangers",
                        "Pipe Insulation & Cladding"
                    ],
                    "Electrical": [
                        "Motor Control Center (MCC)",
                        "Power Distribution Panel",
                        "Instrumentation Cables & Wiring"
                    ],
                    "Instrumentation": [
                        "Pressure Transmitter & Gauge",
                        "Flow Meter - Ultrasonic Type",
                        "Temperature Sensor & Controller"
                    ],
                    "Civil": [
                        "Concrete Foundation & Structures",
                        "Reinforcing Steel Bars",
                        "Structural Steel Framework"
                    ]
                }
                if material_category in material_descriptions:
                    return random.choice(material_descriptions[material_category])
            
            # Generic material items for PROFORMA
            material_items = [
                "Process Equipment & Components",
                "Piping & Pipeline Materials",
                "Instrumentation & Control Systems",
                "Electrical Equipment & Supplies",
                "Structural Steel & Fabrication",
                "Safety & Environmental Equipment",
                "Construction Materials & Supplies",
                "Spare Parts & Maintenance Items",
                "Compressor Units & Accessories",
                "Heat Exchanger Components",
                "Pressure Vessels & Tanks",
                "Control System Hardware",
                "Cabling & Wiring Systems",
                "Mechanical Equipment & Tools"
            ]
            return random.choice(material_items)


def generate_current_invoice_pdfs(cursor, vendors: List[Dict[str, Any]], pos: List[Dict[str, Any]],
                                  sows: List[Dict[str, Any]], projects: List[Dict[str, Any]],
                                  wbs_list: List[Dict[str, Any]], rate_cards: List[Dict[str, Any]],
                                  output_dir: Path, count: int = 20, exception_percentage: float = 0.8,
                                  non_english_pct: float = 0.60, required_non_english_language: Optional[str] = None,
                                  invoice_type_dist: Optional[Dict[str, float]] = None,
                                  project_dir: Optional[Path] = None,
                                  global_memory_only: bool = False) -> List[Dict[str, Any]]:
    """Generate current invoice PDFs with exception scenarios.
    
    Args:
        project_dir: Project directory path. If provided, will prioritize SOWs from global memory.
    """
    if not REPORTLAB_AVAILABLE:
        print("  ⚠ Skipping PDF generation (reportlab not available)")
        return []
    
    invoices_dir = output_dir / "invoices" / "pending"
    invoices_dir.mkdir(parents=True, exist_ok=True)
    
    invoices = []
    base_date = datetime.now() - timedelta(days=10)
    current_year = datetime.now().year
    
    # Distribution based on exception_percentage parameter
    # exception_percentage: 0.0 = all straight-through, 1.0 = all exceptions
    straight_through_percentage = 1.0 - exception_percentage
    # Use round() instead of int() to handle floating-point precision issues
    straight_through_count = max(0, round(count * straight_through_percentage))
    exception_count = count - straight_through_count
    
    # Exception scenarios
    exception_scenarios = [
        "missing_evidence",
        "rate_violation",
        "retention_not_applied",
        "ld_not_applied",
        "wbs_budget_exceeded",
        "abnormal_spikes",
        "multi_factor"
    ]
    
    # Read SOW terms and metadata from global memory (if available)
    sow_terms_from_global = read_sow_terms_from_global_memory(project_dir)
    sow_metadata_from_global = read_sow_metadata_from_global_memory(project_dir)
    sow_numbers_from_global_memory = set(sow_terms_from_global.keys()) if sow_terms_from_global else set()
    sows_from_global = []
    sows_from_global_by_type = {}  # Group by invoice_type: {"LABOR": [sow1, ...], "MATERIAL": [sow2, ...]}
    
    if sow_numbers_from_global_memory:
        print(f"  ✓ Found {len(sow_numbers_from_global_memory)} SOW(s) in global memory: {', '.join(sorted(sow_numbers_from_global_memory))}")
        # Filter SOWs to only use those from global memory for invoice generation
        sows_from_global = [s for s in sows if s.get("sow_number") in sow_numbers_from_global_memory]
        if sows_from_global:
            # Group SOWs by invoice_type
            for sow in sows_from_global:
                invoice_type = sow.get("invoice_type", "PROFORMA")
                if invoice_type not in sows_from_global_by_type:
                    sows_from_global_by_type[invoice_type] = []
                sows_from_global_by_type[invoice_type].append(sow)
            
            # Report which types are available
            type_summary = ", ".join([f"{itype}: {len(sows)}" for itype, sows in sows_from_global_by_type.items()])
            print(f"  → Will use SOW(s) from global memory for invoice generation:")
            print(f"    - SOW numbers: {', '.join([s['sow_number'] for s in sows_from_global])}")
            print(f"    - Invoice types available: {type_summary}")
            if global_memory_only:
                print(f"    - ⚠ global_memory_only=True: Only using global memory SOWs (may not satisfy invoice type/language distribution)")
            else:
                print(f"    - Note: Invoices will only use global memory SOWs if invoice type matches")
        else:
            if global_memory_only:
                print(f"  ⚠ Error: global_memory_only=True but SOW(s) found in global memory are not in generated SOWs list. Cannot generate invoices.")
                return []
            else:
                print(f"  ⚠ Warning: SOW(s) found in global memory but not in generated SOWs list. Will use all SOWs.")
    else:
        if global_memory_only:
            print(f"  ⚠ Error: global_memory_only=True but no SOW terms found in global memory. Cannot generate invoices.")
            return []
        else:
            print(f"  ⚠ No SOW terms found in global memory")
            print(f"  → Will use all generated SOWs for invoice generation")
    
    # If global_memory_only is True, only use SOWs from global memory
    if global_memory_only:
        if not sows_from_global:
            print(f"  ⚠ Error: global_memory_only=True but no SOWs from global memory available. Cannot generate invoices.")
            return []
        # Use only global memory SOWs
        available_sows = sows_from_global
        # Adjust invoice type distribution based on available SOW types
        available_types = list(sows_from_global_by_type.keys())
        if not available_types:
            print(f"  ⚠ Error: global_memory_only=True but no invoice types available from global memory SOWs. Cannot generate invoices.")
            return []
        
        # Count available SOWs by type
        type_counts = {itype: len(sows) for itype, sows in sows_from_global_by_type.items()}
        total_available = len(available_sows)
        
        print(f"  → global_memory_only=True: Using only {total_available} SOW(s) from global memory")
        print(f"    - Available invoice types: {', '.join([f'{itype}: {count}' for itype, count in type_counts.items()])}")
        
        # Adjust invoice count if we don't have enough SOWs
        if total_available < count:
            print(f"  ⚠ Warning: Requested {count} invoices but only {total_available} SOW(s) available. Generating {total_available} invoices.")
            count = total_available
            # Recalculate distribution based on available count
            labor_count = max(0, round(count * invoice_type_dist.get("LABOR", 0.4)))
            material_count = max(0, round(count * invoice_type_dist.get("MATERIAL", 0.4)))
            proforma_count = count - labor_count - material_count
            invoice_type_list = []
            invoice_type_list.extend(["LABOR"] * labor_count)
            invoice_type_list.extend(["MATERIAL"] * material_count)
            invoice_type_list.extend(["PROFORMA"] * proforma_count)
            random.shuffle(invoice_type_list)
    else:
        available_sows = sows
    
    # Get POs that have SOWs (invoices should be linked to SOWs via sow_id)
    # Use available_sows (which may be filtered to global memory only)
    pos_with_sows = [po for po in pos if po.get("sow_id") and any(s["sow_id"] == po.get("sow_id") for s in available_sows)]
    if not pos_with_sows:
        print("  ⚠ Warning: No POs with SOWs found. Cannot generate invoices.")
        return []
    
    # Default distribution: 40% Labor, 40% Material, 20% Proforma
    if invoice_type_dist is None:
        invoice_type_dist = {"LABOR": 0.4, "MATERIAL": 0.4, "PROFORMA": 0.2}
    
    # Normalize distribution
    total = sum(invoice_type_dist.values())
    if total > 0:
        invoice_type_dist = {k: v / total for k, v in invoice_type_dist.items()}
    else:
        invoice_type_dist = {"LABOR": 0.4, "MATERIAL": 0.4, "PROFORMA": 0.2}
    
    # If global_memory_only=True, adjust invoice type distribution based on available SOW types
    if global_memory_only and sows_from_global_by_type:
        available_types = list(sows_from_global_by_type.keys())
        # Filter invoice_type_dist to only include available types
        available_dist = {itype: invoice_type_dist.get(itype, 0) for itype in available_types}
        # Normalize to sum to 1.0
        available_total = sum(available_dist.values())
        if available_total > 0:
            invoice_type_dist = {k: v / available_total for k, v in available_dist.items()}
        else:
            # If no distribution matches, use equal distribution for available types
            invoice_type_dist = {itype: 1.0 / len(available_types) for itype in available_types}
        print(f"  → Adjusted invoice type distribution to match available types: {invoice_type_dist}")
    
    # Calculate counts for each invoice type based on distribution
    labor_count = max(0, round(count * invoice_type_dist.get("LABOR", 0.4)))
    material_count = max(0, round(count * invoice_type_dist.get("MATERIAL", 0.4)))
    proforma_count = max(0, round(count * invoice_type_dist.get("PROFORMA", 0.2)))
    
    # Adjust if total doesn't match count (due to rounding)
    total_assigned = labor_count + material_count + proforma_count
    if total_assigned < count:
        # Distribute remaining to types that have available SOWs
        remaining = count - total_assigned
        if global_memory_only and sows_from_global_by_type:
            # Distribute to available types
            available_types = list(sows_from_global_by_type.keys())
            for i in range(remaining):
                if available_types:
                    type_to_add = available_types[i % len(available_types)]
                    if type_to_add == "LABOR":
                        labor_count += 1
                    elif type_to_add == "MATERIAL":
                        material_count += 1
                    elif type_to_add == "PROFORMA":
                        proforma_count += 1
        else:
            # Distribute evenly
            if "LABOR" in invoice_type_dist:
                labor_count += remaining // 3 + (1 if remaining % 3 >= 1 else 0)
            if "MATERIAL" in invoice_type_dist:
                material_count += remaining // 3 + (1 if remaining % 3 >= 2 else 0)
            if "PROFORMA" in invoice_type_dist:
                proforma_count += remaining - (labor_count + material_count - (count - remaining))
    
    # Create list of invoice types with exact distribution
    invoice_type_list = []
    invoice_type_list.extend(["LABOR"] * labor_count)
    invoice_type_list.extend(["MATERIAL"] * material_count)
    invoice_type_list.extend(["PROFORMA"] * proforma_count)
    random.shuffle(invoice_type_list)  # Shuffle to randomize order
    
    # Create list of all invoice indices and shuffle to randomize order
    # This ensures straight-through and exception invoices are mixed, not always in order
    all_indices = list(range(count))
    random.shuffle(all_indices)
    straight_through_indices = set(all_indices[:straight_through_count])
    
    # Generate invoice numbers with type prefixes - assign based on invoice_type_list
    invoice_number_pools = {
        "LABOR": [],
        "MATERIAL": [],
        "PROFORMA": []
    }
    
    invoice_num_base = 5000
    for idx, invoice_type in enumerate(invoice_type_list):
        invoice_number_pools[invoice_type].append(f"INV-{invoice_type}-{current_year}-{invoice_num_base + idx:04d}")
    
    # Shuffle each pool
    for invoice_type in invoice_number_pools:
        random.shuffle(invoice_number_pools[invoice_type])
    
    # Calculate exact language distribution to match non_english_pct
    # Similar to how we handle exception_percentage, ensure exact distribution
    non_english_count = max(0, round(count * non_english_pct))
    english_count = count - non_english_count
    
    # Validate required_non_english_language if provided
    if required_non_english_language is not None:
        if required_non_english_language not in NON_ENGLISH_LANGUAGES:
            print(f"  ⚠ Warning: required_non_english_language '{required_non_english_language}' is not a valid non-English language. Using random distribution.")
            required_non_english_language = None
        elif required_non_english_language == "en":
            print(f"  ⚠ Warning: required_non_english_language cannot be 'en' (English). Using random distribution.")
            required_non_english_language = None
    
    # Create a list of languages with exact distribution
    language_list = []
    # Add English invoices
    language_list.extend(["en"] * english_count)
    # Add non-English invoices
    if non_english_count > 0:
        if required_non_english_language is not None:
            # Ensure at least one non-English invoice uses the required language
            language_list.append(required_non_english_language)
            # Remaining non-English invoices use random distribution
            remaining_non_english_count = non_english_count - 1
            for i in range(remaining_non_english_count):
                language_list.append(random.choice(NON_ENGLISH_LANGUAGES))
        else:
            # Random distribution for all non-English invoices
            for i in range(non_english_count):
                language_list.append(random.choice(NON_ENGLISH_LANGUAGES))
    # Shuffle to randomize which invoices get which languages
    random.shuffle(language_list)
    
    # Track which language to assign to each invoice (by index)
    language_index = 0
    
    # Generate straight-through invoices
    # Don't sort - process in shuffled order to randomize invoice numbers
    for idx, i in enumerate(all_indices[:straight_through_count]):
        # Get the required invoice type for this invoice based on distribution
        required_invoice_type = invoice_type_list[i] if i < len(invoice_type_list) else random.choice(["LABOR", "MATERIAL", "PROFORMA"])
        
        # For straight-through invoices, we need to select SOWs that:
        # 1. Match the required invoice type
        # 2. Have available milestone cap space (or no milestone cap) to ensure they pass milestone validation
        valid_sows_for_straight_through = []
        max_attempts = 50  # Limit attempts to avoid infinite loop
        attempt = 0
        
        while len(valid_sows_for_straight_through) == 0 and attempt < max_attempts:
            # Filter POs that have SOWs matching the required invoice type
            matching_pos = [po for po in pos_with_sows 
                           if any(s["sow_id"] == po.get("sow_id") and s.get("invoice_type") == required_invoice_type 
                                 for s in available_sows)]
            
            if not matching_pos:
                # If no matching POs, try any PO (fallback)
                matching_pos = pos_with_sows
            
            po = random.choice(matching_pos)
            # Match SOW by sow_id and invoice_type (POs now reference SOWs via sow_id)
            # If we have SOWs from global memory for this invoice type, prioritize those
            if sows_from_global_by_type and required_invoice_type in sows_from_global_by_type:
                # Use type-specific global memory SOWs
                matching_sows = [s for s in sows_from_global_by_type[required_invoice_type] if s["sow_id"] == po.get("sow_id")]
                # If no match, find a PO that matches a global memory SOW of this type
            if not matching_sows:
                    for po_candidate in pos_with_sows:
                        matching_sows = [s for s in sows_from_global_by_type[required_invoice_type] if s["sow_id"] == po_candidate.get("sow_id")]
                        if matching_sows:
                            po = po_candidate
                            break
            elif sows_from_global:
                # Use all global memory SOWs (fallback if type-specific not available)
                # IMPORTANT: Only use global memory SOWs if they match the required invoice type
                # If no match, fall back to all generated SOWs (not global memory SOWs with wrong type)
                matching_sows = [s for s in sows_from_global if s["sow_id"] == po.get("sow_id") and s.get("invoice_type") == required_invoice_type]
                if not matching_sows:
                    # Try to find a PO that matches a global memory SOW with correct invoice type
                    for po_candidate in pos_with_sows:
                        matching_sows = [s for s in sows_from_global if s["sow_id"] == po_candidate.get("sow_id") and s.get("invoice_type") == required_invoice_type]
                        if matching_sows:
                            po = po_candidate
                            break
                # If still no match and not global_memory_only, fall back to all generated SOWs
                if not matching_sows and not global_memory_only:
                    matching_sows = [s for s in available_sows if s["sow_id"] == po.get("sow_id") and s.get("invoice_type") == required_invoice_type]
                    if not matching_sows:
                        matching_sows = [s for s in available_sows if s["sow_id"] == po.get("sow_id")]
            else:
                matching_sows = [s for s in available_sows if s["sow_id"] == po.get("sow_id") and s.get("invoice_type") == required_invoice_type]
                # If no exact match, try without invoice_type filter (only if not global_memory_only or if type not available)
                if not matching_sows:
                    if global_memory_only:
                        # In global_memory_only mode, if required type not available, use any available type
                        if required_invoice_type not in sows_from_global_by_type:
                            # Required type not available, use any available type
                            available_types = list(sows_from_global_by_type.keys())
                            if available_types:
                                # Use first available type
                                fallback_type = available_types[0]
                                matching_sows = [s for s in sows_from_global_by_type[fallback_type] if s["sow_id"] == po.get("sow_id")]
                                if not matching_sows:
                                    # Find any PO that matches this type
                                    for po_candidate in pos_with_sows:
                                        matching_sows = [s for s in sows_from_global_by_type[fallback_type] if s["sow_id"] == po_candidate.get("sow_id")]
                                        if matching_sows:
                                            po = po_candidate
                                            break
                    else:
                        matching_sows = [s for s in available_sows if s["sow_id"] == po.get("sow_id")]
            
            for candidate_sow in matching_sows:
                # Check if this SOW has a milestone cap and if there's space available
                cursor.execute("""
                    SELECT m.milestone_id, m.milestone_cap_amount, m.sow_id
                    FROM milestones m
                    WHERE m.sow_id = ?
                    ORDER BY m.planned_date DESC
                    LIMIT 1
                """, (candidate_sow["sow_id"],))
                milestone_row = cursor.fetchone()
                
                if milestone_row and milestone_row[1]:  # Has milestone cap
                    milestone_cap_limit = float(milestone_row[1])
                    # Get total already billed from historical invoices for this SOW
                    cursor.execute("""
                        SELECT COALESCE(SUM(total_amount), 0) as total_billed
                        FROM historical_invoices
                        WHERE sow_id = ? AND final_status = 'approved'
                    """, (candidate_sow["sow_id"],))
                    billed_row = cursor.fetchone()
                    total_billed_so_far = float(billed_row[0]) if billed_row else 0.0
                    
                    # Check if there's at least 10% of cap remaining (to allow reasonable invoice amount)
                    remaining_cap = milestone_cap_limit - total_billed_so_far
                    if remaining_cap >= milestone_cap_limit * 0.1:  # At least 10% remaining
                        valid_sows_for_straight_through.append((candidate_sow, po))
                else:
                    # No milestone cap - this SOW is valid for straight-through
                    valid_sows_for_straight_through.append((candidate_sow, po))
            
            attempt += 1
        
        if len(valid_sows_for_straight_through) == 0:
            # Fallback: use any SOW (will handle cap issues in invoice amount calculation)
            # If we have SOWs from global memory, prioritize those
            if sows_from_global:
                sow = random.choice(sows_from_global)
                # Find a PO for this SOW
                po = next((p for p in pos_with_sows if p.get("sow_id") == sow["sow_id"]), random.choice(pos_with_sows))
            else:
                po = random.choice(pos_with_sows)
                # Match SOW by sow_id (POs now reference SOWs via sow_id)
                matching_sows = [s for s in sows if s["sow_id"] == po.get("sow_id")]
                sow = random.choice(matching_sows) if matching_sows else None
        else:
            sow, po = random.choice(valid_sows_for_straight_through)
            # If we have SOWs from global memory, ensure we use one of them
            if sows_from_global and sow.get("sow_number") not in sow_numbers_from_global_memory:
                # Replace with a SOW from global memory that matches the invoice type
                matching_global_sows = [s for s in sows_from_global if s.get("invoice_type") == sow.get("invoice_type")]
                if matching_global_sows:
                    sow = random.choice(matching_global_sows)
                    # Find a PO for this SOW
                    po = next((p for p in pos_with_sows if p.get("sow_id") == sow["sow_id"]), po)
        
        if not sow:
            continue  # Skip if no SOW found (shouldn't happen with pos_with_sows filter)
        
        # CRITICAL: For straight-through invoices, vendor MUST match SOW's vendor
        # because rate cards are linked to the SOW's vendor_id, not the PO's vendor_id.
        # If we use a different vendor, the rate card validator won't find matching rate cards.
        sow_vendor_id = sow.get("vendor_id")
        vendor = next((v for v in vendors if v["vendor_id"] == sow_vendor_id), None)
        if not vendor:
            # Fallback: if SOW vendor not found, use PO's vendor (shouldn't happen normally)
            vendor = next((v for v in vendors if v["vendor_id"] == po["vendor_id"]), None)
            if not vendor:
                vendor = random.choice(vendors)
        
        # CRITICAL FIX: For straight-through invoices, always use PO's project to ensure WBS inheritance works
        # The WBS validator inherits WBS from PO line items, so we must use the PO's project
        project = next((p for p in projects if p["project_id"] == po["project_id"]), None)
        if not project:
            project = random.choice(projects)
        
        invoice_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
        # Get invoice type from SOW and generate invoice number with type prefix
        invoice_type = sow.get("invoice_type", "PROFORMA")
        if invoice_number_pools[invoice_type]:
            invoice_number = invoice_number_pools[invoice_type].pop(0)
        else:
            # Fallback: generate with type prefix
            invoice_number = f"INV-{invoice_type}-{current_year}-{5000 + idx:04d}"
        invoice_date = (base_date + timedelta(days=random.randint(0, 5))).strftime("%Y-%m-%d")
        due_date = (datetime.strptime(invoice_date, "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Get PO line items for this PO - invoices should reference PO line items
        cursor.execute("""
            SELECT line_number, item_code, description, quantity, unit_price, total, wbs_id, role, rate, material_category
            FROM po_line_items
            WHERE po_number = ?
            ORDER BY line_number
        """, (po["po_number"],))
        po_line_items_rows = cursor.fetchall()
        po_line_items = []
        for row in po_line_items_rows:
            po_line_items.append({
                "line_number": row[0],
                "item_code": row[1],
                "description": row[2],
                "quantity": row[3],
                "unit_price": row[4],
                "total": row[5],
                "wbs_id": row[6],
                "role": row[7],
                "rate": row[8],
                "material_category": row[9]
            })
        
        # CRITICAL FIX: For straight-through invoices, get WBS from PO line items (not random)
        # The WBS validator inherits WBS from PO line items, so we must use a WBS that exists in the PO line items
        # Find the most common WBS ID from PO line items that have valid WBS IDs
        wbs_id_from_po = None
        if po_line_items:
            # Count WBS IDs from PO line items (only non-None, non-empty ones)
            wbs_id_counts = {}
            for po_line in po_line_items:
                wbs_id = po_line.get("wbs_id")
                if wbs_id:
                    wbs_id_counts[wbs_id] = wbs_id_counts.get(wbs_id, 0) + 1
            
            if wbs_id_counts:
                # Use the most common WBS ID
                wbs_id_from_po = max(wbs_id_counts.items(), key=lambda x: x[1])[0]
        
        # Get WBS object from the WBS ID
        if wbs_id_from_po:
            wbs = next((w for w in wbs_list if w["wbs_id"] == wbs_id_from_po), None)
        
        # Fallback: if no valid WBS from PO line items, use a WBS from the project
        if not wbs:
            wbs = random.choice([w for w in wbs_list if w["project_id"] == project["project_id"]])
        
        # Get rate cards for this SOW (for fallback if no PO line items)
        sow_rate_cards = [rc for rc in rate_cards if rc.get("sow_id") == sow["sow_id"]]
        
        # For LABOR invoices, generate timesheet hours first (before creating line items)
        # This ensures invoice hours match timesheet hours
        timesheet_hours = None
        if invoice_type == "LABOR":
            # Generate realistic timesheet hours (40-80 hours typical for a week)
            timesheet_hours = round(random.uniform(40, 80), 2)
            print(f"  [DEBUG] LABOR invoice {invoice_number}: Generated timesheet_hours = {timesheet_hours}")
        
        # Generate line items based on PO line items and invoice type
        # Proforma invoices are large: 100-200 line items
        # LABOR invoices should have only 1 line item (to match timesheet hours)
        if invoice_type == "PROFORMA":
            num_items = random.randint(100, 200)
        elif invoice_type == "LABOR":
            num_items = 1  # LABOR invoices: single line item with timesheet hours
        else:
            num_items = random.randint(2, 4)
        
        line_items = []
        total_amount = 0.0
        
        # For straight-through invoices, check milestone cap to ensure invoice amount stays within cap
        # This ensures straight-through invoices pass milestone validation
        milestone_cap_limit = None
        total_billed_so_far = 0.0
        
        # Check if there's a milestone cap for this SOW
        cursor.execute("""
            SELECT m.milestone_id, m.milestone_cap_amount, m.sow_id
            FROM milestones m
            WHERE m.sow_id = ?
            ORDER BY m.planned_date DESC
            LIMIT 1
        """, (sow["sow_id"],))
        milestone_row = cursor.fetchone()
        
        if milestone_row and milestone_row[1]:  # milestone_cap_amount exists
            milestone_cap_limit = float(milestone_row[1])
            # Get total already billed from historical invoices for this SOW
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0) as total_billed
                FROM historical_invoices
                WHERE sow_id = ? AND final_status = 'approved'
            """, (milestone_row[2],))  # Use sow_id from milestone
            billed_row = cursor.fetchone()
            total_billed_so_far = float(billed_row[0]) if billed_row else 0.0
        
        # Calculate maximum allowed invoice amount to stay within milestone cap
        # IMPORTANT: The milestone validator checks: total_billed_amount + current_invoice_amount <= milestone_cap_amount
        # So we must ensure: total_billed_so_far + invoice_amount <= milestone_cap_limit
        max_invoice_amount = None
        if milestone_cap_limit is not None:
            remaining_cap = milestone_cap_limit - total_billed_so_far
            if remaining_cap > 0:
                # Use 60-80% of remaining cap to ensure we stay well within limits with safety margin
                # This accounts for potential rounding differences and ensures validation passes
                max_invoice_amount = remaining_cap * random.uniform(0.6, 0.8)
            else:
                # Cap already exceeded by historical invoices - this shouldn't happen for straight-through
                # But if it does, we need to skip this SOW or use a different one
                # For now, set a very small amount, but ideally we should have filtered this out earlier
                max_invoice_amount = 0.01
        
        # Use PO line items if available, otherwise fall back to rate cards
        # CRITICAL FIX: For straight-through invoices, use rate card prices instead of PO line item prices
        # to ensure rate card validation passes
        # CRITICAL FIX: For straight-through invoices, only use PO line items that have valid WBS IDs
        # to ensure WBS inheritance validation passes
        if po_line_items:
            # Filter PO line items to only those with valid WBS IDs (for straight-through invoices)
            po_line_items_with_wbs = [po_line for po_line in po_line_items if po_line.get("wbs_id")]
            
            # If we have PO line items with WBS, use those; otherwise use all PO line items (fallback)
            po_line_items_to_use = po_line_items_with_wbs if po_line_items_with_wbs else po_line_items
            
            # For Proforma, repeat/cycle through PO line items to get enough items
            if invoice_type == "PROFORMA" and len(po_line_items_to_use) < num_items:
                # Repeat PO line items to get enough for 100-200 items
                selected_po_lines = []
                for _ in range(num_items):
                    selected_po_lines.append(random.choice(po_line_items_to_use))
            else:
                # Use available PO line items (may be fewer than requested)
                selected_po_lines = random.sample(po_line_items_to_use, min(num_items, len(po_line_items_to_use))) if po_line_items_to_use else []
            
            for line_idx, po_line in enumerate(selected_po_lines):
                if max_invoice_amount is not None and total_amount >= max_invoice_amount:
                    # Already reached the cap limit, stop adding line items
                    break
                
                # For LABOR invoices, use timesheet hours as quantity (ensures invoice hours match timesheet)
                if invoice_type == "LABOR" and timesheet_hours is not None:
                    # Distribute timesheet hours across line items (for first item, use all hours; for others, use 0)
                    if line_idx == 0:
                        quantity = timesheet_hours
                        print(f"  [DEBUG] LABOR invoice {invoice_number} line {line_idx + 1}: Set quantity = {quantity} from timesheet_hours")
                    else:
                        quantity = 0.0  # Additional line items have 0 hours (for multi-line LABOR invoices)
                        print(f"  [DEBUG] LABOR invoice {invoice_number} line {line_idx + 1}: Set quantity = 0.0 (additional line item)")
                else:
                    # Use PO line item data, but adjust quantity/price for invoice
                    quantity = po_line["quantity"] * random.uniform(0.8, 1.2)  # Invoice quantity may differ slightly
                    if invoice_type == "LABOR":
                        print(f"  [DEBUG] LABOR invoice {invoice_number} line {line_idx + 1}: Using PO quantity={quantity} (timesheet_hours={timesheet_hours})")
                
                # CRITICAL FIX: For straight-through invoices, use rate card price instead of PO price
                # to ensure rate card validation passes (rate card validator expects invoice price to match rate card price)
                unit_price = po_line["unit_price"]  # Default to PO price
                item_code_to_use = po_line["item_code"]  # Default to PO item_code
                if sow_rate_cards:
                    # Try to find matching rate card by item_code
                    matching_rate = next((rc for rc in sow_rate_cards if rc.get("item_code") == po_line["item_code"]), None)
                    if matching_rate:
                        # Use rate card price to ensure validation passes
                        unit_price = matching_rate["unit_price"]
                    else:
                        # No matching rate card found - use a rate card from the SOW (any one)
                        # This ensures the invoice price matches a rate card for validation
                        matching_rate = random.choice(sow_rate_cards)
                        unit_price = matching_rate["unit_price"]
                        item_code_to_use = matching_rate["item_code"]  # Update item_code to match rate card
                
                line_total = round(quantity * unit_price, 2)
                
                # If adding this line item would exceed the cap, reduce quantity
                # EXCEPTION: For LABOR invoices, preserve timesheet_hours (don't override quantity)
                if max_invoice_amount is not None and (total_amount + line_total) > max_invoice_amount:
                    # For LABOR invoices with timesheet_hours, preserve the hours even if it exceeds cap
                    # (This ensures invoice hours match timesheet hours)
                    if invoice_type == "LABOR" and timesheet_hours is not None and line_idx == 0:
                        # Keep the timesheet_hours quantity, but recalculate line_total
                        line_total = round(quantity * unit_price, 2)
                    else:
                        # Calculate max quantity that fits within cap
                        max_line_total = max_invoice_amount - total_amount
                        if max_line_total > 0:
                            quantity = max_line_total / unit_price
                            line_total = round(quantity * unit_price, 2)
                        else:
                            # No room left, skip this line item
                            break
                
                total_amount += line_total
                
                # Generate intelligent description based on invoice type and PO line item data
                description = _generate_line_item_description(
                    invoice_type, 
                    item_code_to_use,  # Use updated item_code if rate card was used
                    role=po_line.get("role"),
                    material_category=po_line.get("material_category"),
                    line_num=line_idx + 1
                )
                
                final_quantity = round(quantity, 2)
                print(f"  [DEBUG] Invoice {invoice_number} line {line_idx + 1}: Final quantity={final_quantity}, unit_price={unit_price}, line_total={line_total}")
                line_items.append({
                    "line_number": line_idx + 1,
                    "item_code": item_code_to_use,  # Use updated item_code if rate card was used
                    "description": description,
                    "quantity": final_quantity,
                    "unit_price": unit_price,
                    "total": line_total,
                    "po_reference": po["po_number"],
                    "po_line_number": po_line["line_number"]
                })
        else:
            # Fallback: use rate cards if no PO line items available
            if invoice_type == "PROFORMA" and sow_rate_cards:
                # Repeat rate cards to get enough for 100-200 items
                selected_rates = []
                for _ in range(num_items):
                    selected_rates.append(random.choice(sow_rate_cards))
            else:
                selected_rates = random.sample(sow_rate_cards, min(num_items, len(sow_rate_cards))) if sow_rate_cards else []
            
            for line_idx, rate in enumerate(selected_rates):
                if max_invoice_amount is not None and total_amount >= max_invoice_amount:
                    # Already reached the cap limit, stop adding line items
                    break
                
                # For LABOR invoices, use timesheet hours as quantity (ensures invoice hours match timesheet)
                if invoice_type == "LABOR" and timesheet_hours is not None:
                    # For first line item, use all timesheet hours; for others, use 0
                    if line_idx == 0:
                        quantity = timesheet_hours
                        print(f"  [DEBUG] LABOR invoice {invoice_number} (rate card fallback) line {line_idx + 1}: Set quantity = {quantity} from timesheet_hours")
                    else:
                        quantity = 0.0  # Additional line items have 0 hours (for multi-line LABOR invoices)
                        print(f"  [DEBUG] LABOR invoice {invoice_number} (rate card fallback) line {line_idx + 1}: Set quantity = 0.0 (additional line item)")
                else:
                    quantity = random.uniform(10, 50)
                    if invoice_type == "LABOR":
                        print(f"  [DEBUG] LABOR invoice {invoice_number} (rate card fallback) line {line_idx + 1}: Using random quantity={quantity} (timesheet_hours={timesheet_hours})")
                
                unit_price = rate["unit_price"]  # Use rate card price (no violation)
                line_total = round(quantity * unit_price, 2)
                print(f"  [DEBUG] Invoice {invoice_number} (rate card fallback) line {line_idx + 1}: quantity={quantity}, unit_price={unit_price}, line_total={line_total}")
                
                # If adding this line item would exceed the cap, reduce quantity
                # EXCEPTION: For LABOR invoices, preserve timesheet_hours (don't override quantity)
                if max_invoice_amount is not None and (total_amount + line_total) > max_invoice_amount:
                    # For LABOR invoices with timesheet_hours, preserve the hours even if it exceeds cap
                    # (This ensures invoice hours match timesheet hours)
                    if invoice_type == "LABOR" and timesheet_hours is not None and line_idx == 0:
                        # Keep the timesheet_hours quantity, but recalculate line_total
                        line_total = round(quantity * unit_price, 2)
                    else:
                        # Calculate max quantity that fits within cap
                        max_line_total = max_invoice_amount - total_amount
                        if max_line_total > 0:
                            quantity = max_line_total / unit_price
                            line_total = round(quantity * unit_price, 2)
                        else:
                            # No room left, skip this line item
                            break
                
                total_amount += line_total
                
                # Generate intelligent description
                description = _generate_line_item_description(
                    invoice_type,
                    rate["item_code"],
                    line_num=line_idx + 1
                )
                
                line_items.append({
                    "line_number": line_idx + 1,
                    "item_code": rate["item_code"],
                    "description": description,
                    "quantity": round(quantity, 2),
                    "unit_price": unit_price,
                    "total": line_total,
                    "po_reference": po["po_number"],
                    "po_line_number": None  # No PO line item reference available
                })
        
        # Final safety check: Ensure total_amount doesn't exceed max_invoice_amount
        # This accounts for any rounding differences
        if max_invoice_amount is not None and total_amount > max_invoice_amount:
            # CRITICAL FIX: For LABOR invoices with timesheet_hours, skip cap reduction to preserve quantity
            # The timesheet_hours must match the invoice quantity, so we cannot reduce quantity
            # Note: This may cause the invoice to exceed milestone cap, but timesheet_hours must be preserved
            # The milestone cap should be set high enough to accommodate LABOR invoices with timesheet_hours
            if invoice_type == "LABOR" and timesheet_hours is not None:
                # Skip cap reduction for LABOR invoices with timesheet_hours to preserve quantity
                # This ensures invoice hours match timesheet hours for validation
                pass
            else:
                # For non-LABOR invoices, reduce the last line item to fit within the cap
                if line_items:
                    excess = total_amount - max_invoice_amount
                    last_item = line_items[-1]
                    last_item["total"] = max(0.01, round(last_item["total"] - excess, 2))
                    # Recalculate quantity if needed
                    if last_item["unit_price"] > 0:
                        last_item["quantity"] = round(last_item["total"] / last_item["unit_price"], 2)
                    total_amount = sum(item["total"] for item in line_items)
        
        # CRITICAL FIX: For straight-through invoices, ensure amount is NOT abnormally high to prevent abnormal_spike detection
        # The anomaly validator checks if invoice amount exceeds 1.5x the average historical amount for the vendor/SOW
        vendor_name = vendor.get("vendor_name", "")
        sow_number = sow.get("sow_number", "")
        
        cursor.execute("""
            SELECT AVG(hi.total_amount) as avg_amount, MAX(hi.total_amount) as max_amount, COUNT(*) as count
            FROM historical_invoices hi
            JOIN vendors v ON hi.vendor_id = v.vendor_id
            JOIN statements_of_work s ON hi.sow_id = s.sow_id
            WHERE v.vendor_name = ? AND s.sow_number = ? AND hi.final_status = 'approved'
        """, (vendor_name, sow_number))
        hist_row = cursor.fetchone()
        
        if hist_row and hist_row[2] and hist_row[2] > 0:  # count is at index 2
            avg_amount = float(hist_row[0]) if hist_row[0] else 0.0  # avg_amount is at index 0
            max_amount = float(hist_row[1]) if hist_row[1] else 0.0  # max_amount is at index 1
            
            # Ensure amount is within normal range (not more than 1.4x average to stay below 1.5x threshold)
            # The anomaly validator threshold is 1.5x (50% variance), so we need to stay below that
            max_normal_amount = avg_amount * 1.4 if avg_amount > 0 else total_amount
            if total_amount > max_normal_amount:
                # CRITICAL FIX: For LABOR invoices with timesheet_hours, skip scaling to preserve timesheet_hours quantity
                # The timesheet_hours must match the invoice quantity, so we cannot scale it down
                # Instead, we rely on historical data having similar amounts to keep the average reasonable
                if invoice_type == "LABOR" and timesheet_hours is not None:
                    # Skip scaling for LABOR invoices with timesheet_hours to preserve quantity
                    # This ensures invoice hours match timesheet hours for validation
                    pass
                else:
                    # Reduce amount to stay within normal range for non-LABOR invoices
                    scale_factor = max_normal_amount / total_amount
                    for item in line_items:
                        item["quantity"] = round(item["quantity"] * scale_factor, 2)
                        item["total"] = round(item["unit_price"] * item["quantity"], 2)
                    total_amount = sum(item["total"] for item in line_items)
        
        # Apply retention if SOW has it
        retention_percentage = sow.get("retention_percentage", 0)
        retention_applied = True
        
        # Apply LD if applicable and milestone is late
        ld_applicable = sow.get("ld_applicable", False)
        ld_amount = 0
        ld_applied = True
        
        # For straight-through invoices, calculate LD if applicable and milestone is late
        if ld_applicable:
            cursor.execute("""
                SELECT planned_date, actual_date FROM milestones 
                WHERE sow_id = ? AND actual_date IS NOT NULL AND planned_date IS NOT NULL
                    AND actual_date > planned_date
                ORDER BY planned_date DESC LIMIT 1
            """, (sow["sow_id"],))
            milestone_result = cursor.fetchone()
            if milestone_result and milestone_result[1]:
                planned = datetime.strptime(milestone_result[0], "%Y-%m-%d")
                actual = datetime.strptime(milestone_result[1], "%Y-%m-%d")
                if actual > planned:
                    days_late = (actual - planned).days
                    ld_rate = sow.get("ld_rate_per_day", 0)
                    ld_amount = round(days_late * ld_rate, 2)
                    ld_applied = True
        
        # Assign language: Check SOW metadata from global memory first, then fallback to English (especially for global_memory_only)
        language = "en"  # Default to English
        sow_number = sow.get("sow_number")
        if sow_metadata_from_global and sow_number and sow_number in sow_metadata_from_global:
            # Check if SOW metadata has language field
            sow_metadata = sow_metadata_from_global[sow_number]
            if "language" in sow_metadata and sow_metadata["language"]:
                language = sow_metadata["language"]
            # If no language in metadata, default to English (don't use distribution list for global_memory_only)
        # If no SOW metadata, default to English (don't randomize for global_memory_only scenario)
        
        invoice_data = {
            "invoice_number": invoice_number,
            "vendor_name": vendor["vendor_name"],
            "invoice_date": invoice_date,
            "due_date": due_date,
            "po_reference": po["po_number"],
            "sow_reference": sow["sow_number"],
            "project_reference": project["project_code"],
            "wbs_reference": wbs["wbs_code"],
            "line_items": line_items,
            "total_amount": round(total_amount, 2),
            "tax_amount": 0,
            "retention_percentage": retention_percentage,
            "retention_applied": retention_applied,
            "ld_applicable": ld_applicable,
            "ld_amount": ld_amount,
            "ld_applied": ld_applied,
            "evidence_references": _get_evidence_references_for_invoice_type(invoice_type, invoice_number)
        }
        
        # Store timesheet hours in invoice_data for evidence generation (LABOR invoices only)
        if invoice_type == "LABOR" and timesheet_hours is not None:
            invoice_data["timesheet_hours"] = timesheet_hours
        
        # Debug: Print line_items before PDF generation
        print(f"  [DEBUG] Invoice {invoice_number} before PDF generation: line_items={invoice_data['line_items']}")
        print(f"  [DEBUG] Invoice {invoice_number} before PDF generation: total_amount={invoice_data['total_amount']}")
        
        filepath = generate_invoice_pdf(invoices_dir, invoice_data, language=language)
        
        # Create file tracking record with language
        # For straight-through invoices, scenario_type is "straight_through" and exception_flags is empty
        scenario_type = "straight_through"
        exception_flags = {}
        
        cursor.execute("""
            INSERT INTO incoming_invoices (invoice_id, invoice_file_path, status, document_language, submitted_at, scenario_type, exception_flags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (invoice_id, str(filepath), "pending", language, datetime.now().isoformat(), 
              scenario_type, json.dumps(exception_flags)))
        
        invoices.append({
            "invoice_id": invoice_id,
            "invoice_number": invoice_number,
            "vendor_id": vendor["vendor_id"],
            "po_number": po["po_number"],
            "sow_id": sow["sow_id"],
            "project_id": project["project_id"],
            "total_amount": invoice_data["total_amount"],
            "scenario_type": scenario_type,
            "exception_flags": exception_flags,
            "invoice_data": invoice_data,
            "document_language": language
        })
    
    # Generate exception invoices
    # NEW APPROACH: Randomly select 0-N exceptions per invoice
    # For each invoice, randomly decide which exceptions should be present
    # Then ensure ONLY those exception conditions are met, and all others are NOT met
    exception_indices = [i for i in range(count) if i not in straight_through_indices]
    # Use remaining invoice numbers from shuffled list
    
    # Define all possible exception types
    # Note: wbs_budget_exceeded was renamed from milestone_cap_exceeded
    all_exception_types = [
        "rate_violation",
        "missing_evidence",
        "retention_not_applied",
        "ld_not_applied",
        "wbs_budget_exceeded",
        "abnormal_spike"
    ]
    
    for idx, i in enumerate(exception_indices):
        # Get the required invoice type for this invoice based on distribution
        required_invoice_type = invoice_type_list[i] if i < len(invoice_type_list) else random.choice(["LABOR", "MATERIAL", "PROFORMA"])
        
        # CRITICAL FIX: Filter exception types based on invoice type
        # LABOR: Only rate_violation, missing_evidence, abnormal_spike
        # MATERIAL: Only missing_evidence, wbs_budget_exceeded, abnormal_spike
        # PROFORMA: All 6 exception types
        if required_invoice_type == "LABOR":
            # LABOR invoices: Only rate_violation, missing_evidence, abnormal_spike
            available_exception_types = ["rate_violation", "missing_evidence", "abnormal_spike"]
        elif required_invoice_type == "MATERIAL":
            # MATERIAL invoices: Only missing_evidence, wbs_budget_exceeded, abnormal_spike
            available_exception_types = ["missing_evidence", "wbs_budget_exceeded", "abnormal_spike"]
        else:
            # PROFORMA invoices: All exception types
            available_exception_types = all_exception_types.copy()
        
        # Randomly select 1-3 exceptions for this invoice (to get variety)
        # Weighted: 40% single exception, 40% two exceptions, 20% three exceptions
        num_exceptions = random.choices([1, 2, 3], weights=[40, 40, 20])[0]
        # Ensure we don't select more exceptions than available
        num_exceptions = min(num_exceptions, len(available_exception_types))
        selected_exceptions = set(random.sample(available_exception_types, num_exceptions))
        
        # Determine scenario_type for backward compatibility (use first exception or "multi_factor")
        if len(selected_exceptions) == 1:
            scenario_type = list(selected_exceptions)[0]
        else:
            scenario_type = "multi_factor"
        
        # Find a SOW that can support the selected exceptions
        # Requirements:
        # - rate_violation: needs rate cards (but will violate them)
        # - missing_evidence: needs rate cards (to avoid rate_violation)
        # - retention_not_applied: needs SOW with retention_percentage > 0
        # - ld_not_applied: needs SOW with ld_applicable = True and milestones
        # - wbs_budget_exceeded: needs SOW with milestone caps
        # - abnormal_spike: needs historical data (or SOW without milestone cap to avoid wbs_budget_exceeded)
        
        compatible_sows = []
        # If global_memory_only=True, only use global memory SOWs
        # Otherwise, prioritize global memory but allow fallback
        if global_memory_only:
            sow_list_to_use = sows_from_global if sows_from_global else []
        else:
            sow_list_to_use = sows_from_global if sows_from_global else available_sows
        
        for po_candidate in pos_with_sows:
            # Match SOW by sow_id and invoice_type (POs now reference SOWs via sow_id)
            matching_sows_candidate = [s for s in sow_list_to_use if s["sow_id"] == po_candidate.get("sow_id") and s.get("invoice_type") == required_invoice_type]
            # If no exact match, try without invoice_type filter
            if not matching_sows_candidate:
                matching_sows_candidate = [s for s in sow_list_to_use if s["sow_id"] == po_candidate.get("sow_id")]
            for sow_candidate in matching_sows_candidate:
                # Check if SOW has rate cards (needed for most scenarios, except rate_violation which will violate them)
                sow_rate_cards_check = [rc for rc in rate_cards if rc.get("sow_id") == sow_candidate["sow_id"]]
                has_rate_cards = len(sow_rate_cards_check) >= 2
                
                # Check SOW properties
                has_retention = sow_candidate.get("retention_percentage", 0) > 0
                has_ld = sow_candidate.get("ld_applicable", False)
                
                # Check milestone cap
                cursor.execute("""
                    SELECT milestone_cap_amount FROM milestones 
                    WHERE sow_id = ? AND approval_status = 'approved'
                    ORDER BY planned_date DESC LIMIT 1
                """, (sow_candidate["sow_id"],))
                milestone_result = cursor.fetchone()
                has_milestone_cap = milestone_result and milestone_result[0]
                
                # Check if SOW has milestones
                cursor.execute("""
                    SELECT milestone_id FROM milestones 
                    WHERE sow_id = ? LIMIT 1
                """, (sow_candidate["sow_id"],))
                has_milestones = cursor.fetchone() is not None
                
                # Check if this SOW is compatible with selected exceptions
                is_compatible = True
                
                # If rate_violation is NOT selected, we need valid rate cards
                if "rate_violation" not in selected_exceptions and not has_rate_cards:
                    is_compatible = False
                
                # If retention_not_applied is selected, we need retention
                if "retention_not_applied" in selected_exceptions and not has_retention:
                    is_compatible = False
                
                # If ld_not_applied is selected, we need LD and milestones
                if "ld_not_applied" in selected_exceptions and (not has_ld or not has_milestones):
                    is_compatible = False
                
                # If wbs_budget_exceeded is selected, we need milestone cap AND WBS assignments on PO line items
                if "wbs_budget_exceeded" in selected_exceptions:
                    if not has_milestone_cap:
                        is_compatible = False
                    else:
                        # Check if PO line items have WBS assignments
                        cursor.execute("""
                            SELECT COUNT(*) FROM po_line_items
                            WHERE po_number = ? AND wbs_id IS NOT NULL
                        """, (po_candidate["po_number"],))
                        wbs_count = cursor.fetchone()[0]
                        if wbs_count == 0:
                            is_compatible = False  # No WBS assignments on PO line items
                
                # If abnormal_spike is selected but wbs_budget_exceeded is NOT, prefer no milestone cap
                # (to avoid accidentally triggering wbs_budget_exceeded)
                if "abnormal_spike" in selected_exceptions and "wbs_budget_exceeded" not in selected_exceptions:
                    if has_milestone_cap:
                        # Still compatible, but we'll need to be careful with amounts
                        pass
                
                if is_compatible:
                    compatible_sows.append((po_candidate, sow_candidate))
        
        # Select a compatible SOW
        # Since we regenerate all data every time, there should always be SOWs available
        # We'll prefer compatible SOWs, but fall back to any matching SOW if needed
        # For exceptions, we can generate the conditions programmatically even if SOW doesn't have all properties
        # Strategy: Try to find SOWs that support at least SOME of the selected exceptions
        if compatible_sows:
            # If we have SOWs from global memory, prioritize those
            if sows_from_global:
                global_compatible = [(p, s) for p, s in compatible_sows if s.get("sow_number") in sow_numbers_from_global_memory]
                if global_compatible:
                    po, sow = random.choice(global_compatible)
                else:
                    po, sow = random.choice(compatible_sows)
            else:
                po, sow = random.choice(compatible_sows)
        else:
            # Fallback: Find SOWs that can support at least some exceptions
            # Priority: missing_evidence and rate_violation can work with any SOW
            # For others, we'll generate conditions programmatically where possible
            partial_compatible_sows = []
            # Use type-specific global memory SOWs if available
            # IMPORTANT: Only use global memory SOWs if they match the required invoice type
            if global_memory_only:
                # In global_memory_only mode, only use global memory SOWs
                if sows_from_global_by_type and required_invoice_type in sows_from_global_by_type:
                    sow_list_for_partial = sows_from_global_by_type[required_invoice_type]
                elif sows_from_global:
                    # Use any global memory SOW if type-specific not available
                    sow_list_for_partial = [s for s in sows_from_global if s.get("invoice_type") == required_invoice_type]
                    if not sow_list_for_partial:
                        # If required type not available, use any available type
                        available_types = list(sows_from_global_by_type.keys())
                        if available_types:
                            sow_list_for_partial = sows_from_global_by_type[available_types[0]]
                        else:
                            sow_list_for_partial = sows_from_global
                else:
                    sow_list_for_partial = []
            else:
                # Not global_memory_only: use type-specific global memory SOWs if available, otherwise all SOWs
                if sows_from_global_by_type and required_invoice_type in sows_from_global_by_type:
                    sow_list_for_partial = sows_from_global_by_type[required_invoice_type]
                else:
                    sow_list_for_partial = available_sows
            
            for po_candidate in pos_with_sows:
                matching_sows_candidate = [s for s in sow_list_for_partial if s["sow_id"] == po_candidate.get("sow_id") and s.get("invoice_type") == required_invoice_type]
                if not matching_sows_candidate:
                    matching_sows_candidate = [s for s in sow_list_for_partial if s["sow_id"] == po_candidate.get("sow_id")]
                for sow_candidate in matching_sows_candidate:
                    sow_rate_cards_check = [rc for rc in rate_cards if rc.get("sow_id") == sow_candidate["sow_id"]]
                    has_rate_cards = len(sow_rate_cards_check) >= 2
                    has_retention = sow_candidate.get("retention_percentage", 0) > 0
                    has_ld = sow_candidate.get("ld_applicable", False)
                    
                    # Check if this SOW can support at least one selected exception
                    can_support_any = False
                    if "missing_evidence" in selected_exceptions or "rate_violation" in selected_exceptions:
                        can_support_any = True  # These work with any SOW
                    elif "retention_not_applied" in selected_exceptions and has_retention:
                        can_support_any = True
                    elif "ld_not_applied" in selected_exceptions and has_ld:
                        can_support_any = True
                    elif "abnormal_spike" in selected_exceptions:
                        can_support_any = True  # Can generate programmatically
                    elif has_rate_cards:  # If has rate cards, can support most exceptions
                        can_support_any = True
                    
                    if can_support_any:
                        partial_compatible_sows.append((po_candidate, sow_candidate))
                        break
            
            if partial_compatible_sows:
                # If we have SOWs from global memory, prioritize those
                if sows_from_global:
                    global_compatible = [(p, s) for p, s in partial_compatible_sows if s.get("sow_number") in sow_numbers_from_global_memory]
                    if global_compatible:
                        po, sow = random.choice(global_compatible)
                    else:
                        po, sow = random.choice(partial_compatible_sows)
                else:
                    po, sow = random.choice(partial_compatible_sows)
            else:
                # Final fallback: use any PO/SOW matching invoice type
                # If we have SOWs from global memory, prioritize those
                if sows_from_global:
                    matching_pos = [po for po in pos_with_sows 
                                   if any(s["sow_id"] == po.get("sow_id") and s.get("invoice_type") == required_invoice_type 
                                         for s in sows_from_global)]
                    if not matching_pos:
                        matching_pos = [po for po in pos_with_sows 
                                       if any(s["sow_id"] == po.get("sow_id") for s in sows_from_global)]
                    if not matching_pos:
                        matching_pos = pos_with_sows
                    
                    po = random.choice(matching_pos)
                    matching_sows = [s for s in sows_from_global if s["sow_id"] == po.get("sow_id") and s.get("invoice_type") == required_invoice_type]
                    # IMPORTANT: If no matching SOW from global memory with correct invoice type, fall back to all generated SOWs
                    if not matching_sows:
                        # Try all generated SOWs (not global memory with wrong type)
                        matching_sows = [s for s in sows if s["sow_id"] == po.get("sow_id") and s.get("invoice_type") == required_invoice_type]
                        if not matching_sows:
                            matching_sows = [s for s in sows if s["sow_id"] == po.get("sow_id")]
                    
                    if matching_sows:
                        sow = random.choice(matching_sows)
                    else:
                        # Final fallback: use any SOW that matches invoice type (prefer global memory if type matches)
                        matching_sows = [s for s in sows if s.get("invoice_type") == required_invoice_type]
                        if matching_sows:
                            sow = random.choice(matching_sows)
                            po = next((p for p in pos_with_sows if p.get("sow_id") == sow["sow_id"]), random.choice(pos_with_sows))
                        else:
                            # Last resort: use any SOW
                            sow = random.choice(sows)
                            po = next((p for p in pos_with_sows if p.get("sow_id") == sow["sow_id"]), random.choice(pos_with_sows))
                else:
                    matching_pos = [po for po in pos_with_sows 
                               if any(s["sow_id"] == po.get("sow_id") and s.get("invoice_type") == required_invoice_type 
                                     for s in sows)]
                if not matching_pos:
                    matching_pos = pos_with_sows
                
                po = random.choice(matching_pos)
                matching_sows = [s for s in sows if s["sow_id"] == po.get("sow_id") and s.get("invoice_type") == required_invoice_type]
                if not matching_sows:
                    matching_sows = [s for s in sows if s["sow_id"] == po.get("sow_id")]
                
                if not matching_sows:
                    print(f"  ⚠ Warning: PO {po.get('po_number')} has no matching SOW, skipping invoice")
                    continue
                
                sow = random.choice(matching_sows)
        
        # Ensure SOW has rate cards (except for rate_violation and missing_evidence which don't require them)
        # This prevents unintended rate violations for other exception scenarios
        # For missing_evidence exceptions, we don't need rate cards - we can generate the invoice without them
        if "rate_violation" not in selected_exceptions and "missing_evidence" not in selected_exceptions:
            sow_rate_cards_check = [rc for rc in rate_cards if rc.get("sow_id") == sow["sow_id"]]
            if len(sow_rate_cards_check) < 2:  # Need at least 2 rate cards for invoice
                # Try to find another SOW with rate cards
                matching_pos_with_rates = [po for po in pos_with_sows 
                                          if any(s["sow_id"] == po.get("sow_id") and 
                                                len([rc for rc in rate_cards if rc.get("sow_id") == s["sow_id"]]) >= 2
                                                for s in sows if s["sow_id"] == po.get("sow_id"))]
                if matching_pos_with_rates:
                    po = random.choice(matching_pos_with_rates)
                    matching_sows = [s for s in sows if s["sow_id"] == po.get("sow_id")]
                    if matching_sows:
                        sow = random.choice(matching_sows)
                    else:
                        continue  # Skip if still no SOW
                else:
                    continue  # Skip if no POs with SOWs that have rate cards
        
        # For exception invoices, use SOW's vendor to ensure rate cards can be found
        # (unless rate_violation is selected, in which case vendor mismatch might be intentional)
        # Rate cards are linked to SOW's vendor_id, so invoice vendor should match for validation
        if "rate_violation" not in selected_exceptions:
            # For non-rate-violation exceptions, use SOW's vendor to ensure rate cards are found
            sow_vendor_id = sow.get("vendor_id")
            vendor = next((v for v in vendors if v["vendor_id"] == sow_vendor_id), None)
            if not vendor:
                # Fallback: use PO's vendor
                vendor = next((v for v in vendors if v["vendor_id"] == po["vendor_id"]), None)
                if not vendor:
                    vendor = random.choice(vendors)
        else:
            # For rate_violation exceptions, vendor mismatch might be intentional
            # But still prefer SOW's vendor for consistency
            sow_vendor_id = sow.get("vendor_id")
            vendor = next((v for v in vendors if v["vendor_id"] == sow_vendor_id), None)
            if not vendor:
                vendor = next((v for v in vendors if v["vendor_id"] == po["vendor_id"]), None)
                if not vendor:
                    vendor = random.choice(vendors)
        
        # Randomly choose whether to use PO's project or a random project
        if random.random() < 0.7:  # 70% use PO's project, 30% random
            project = next((p for p in projects if p["project_id"] == po["project_id"]), None)
        else:
            project = random.choice(projects)
        
        if not project:
            project = random.choice(projects)
        
        wbs = random.choice([w for w in wbs_list if w["project_id"] == project["project_id"]])
        
        # 20-30% span multiple projects
        additional_projects = []
        if random.random() < 0.25:
            other_projects = [p for p in projects if p["project_id"] != project["project_id"]]
            if other_projects:
                additional_proj = random.choice(other_projects)
                additional_wbs = random.choice([w for w in wbs_list if w["project_id"] == additional_proj["project_id"]])
                additional_projects.append({
                    "project_code": additional_proj["project_code"],
                    "wbs_code": additional_wbs["wbs_code"]
                })
        
        invoice_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
        # Use the required invoice type (already determined from distribution)
        invoice_type = required_invoice_type
        if invoice_number_pools[invoice_type]:
            invoice_number = invoice_number_pools[invoice_type].pop(0)
        else:
            # Fallback: generate with type prefix
            invoice_number = f"INV-{invoice_type}-{current_year}-{5000 + idx:04d}"
        invoice_date = (base_date + timedelta(days=random.randint(0, 5))).strftime("%Y-%m-%d")
        due_date = (datetime.strptime(invoice_date, "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Get PO line items for this PO - invoices should reference PO line items
        cursor.execute("""
            SELECT line_number, item_code, description, quantity, unit_price, total, wbs_id, role, rate, material_category
            FROM po_line_items
            WHERE po_number = ?
            ORDER BY line_number
        """, (po["po_number"],))
        po_line_items_rows = cursor.fetchall()
        po_line_items = []
        for row in po_line_items_rows:
            po_line_items.append({
                "line_number": row[0],
                "item_code": row[1],
                "description": row[2],
                "quantity": row[3],
                "unit_price": row[4],
                "total": row[5],
                "wbs_id": row[6],
                "role": row[7],
                "rate": row[8],
                "material_category": row[9]
            })
        
        # Get rate cards for this SOW (for fallback if no PO line items)
        sow_rate_cards = [rc for rc in rate_cards if rc.get("sow_id") == sow["sow_id"]]
        
        # For LABOR invoices, generate timesheet hours first (before creating line items)
        # This ensures invoice hours match timesheet hours
        timesheet_hours = None
        if invoice_type == "LABOR":
            # Generate realistic timesheet hours (40-80 hours typical for a week)
            timesheet_hours = round(random.uniform(40, 80), 2)
        
        # Generate line items based on PO line items and invoice type
        # Proforma invoices are large: 100-200 line items
        # LABOR invoices should have only 1 line item (to match timesheet hours)
        if invoice_type == "PROFORMA":
            num_items = random.randint(100, 200)
        elif invoice_type == "LABOR":
            num_items = 1  # LABOR invoices: single line item with timesheet hours
        else:
            num_items = random.randint(2, 4)
        
        line_items = []
        total_amount = 0.0
        exception_flags = {}
        
        # Use PO line items if available, otherwise fall back to rate cards
        if po_line_items:
            # For Proforma, repeat/cycle through PO line items to get enough items
            if invoice_type == "PROFORMA" and len(po_line_items) < num_items:
                # Repeat PO line items to get enough for 100-200 items
                selected_po_lines = []
                for _ in range(num_items):
                    selected_po_lines.append(random.choice(po_line_items))
            else:
                # Use available PO line items (may be fewer than requested)
                selected_po_lines = random.sample(po_line_items, min(num_items, len(po_line_items))) if po_line_items else []
            
            for line_idx, po_line in enumerate(selected_po_lines):
                # For LABOR invoices, use timesheet hours as quantity (ensures invoice hours match timesheet)
                if invoice_type == "LABOR" and timesheet_hours is not None:
                    # Distribute timesheet hours across line items (for first item, use all hours; for others, use 0)
                    if line_idx == 0:
                        quantity = timesheet_hours
                    else:
                        quantity = 0.0  # Additional line items have 0 hours (for multi-line LABOR invoices)
                else:
                    # Use PO line item data, but adjust quantity/price for invoice
                    quantity = po_line["quantity"] * random.uniform(0.8, 1.2)  # Invoice quantity may differ slightly
                
                # Rate violation: charge above PO price (if selected)
                if "rate_violation" in selected_exceptions:
                    unit_price = po_line["unit_price"] * random.uniform(1.06, 1.15)  # 6-15% above
                    exception_flags["rate_violation"] = True
                else:
                    # NOT selected: use valid PO price to prevent rate_violation
                    unit_price = po_line["unit_price"]
                
                line_total = round(quantity * unit_price, 2)
                total_amount += line_total
                
                # Generate intelligent description based on invoice type and PO line item data
                description = _generate_line_item_description(
                    invoice_type, 
                    po_line["item_code"],
                    role=po_line.get("role"),
                    material_category=po_line.get("material_category"),
                    line_num=line_idx + 1
                )
                
                line_items.append({
                    "line_number": line_idx + 1,
                    "item_code": po_line["item_code"],
                    "description": description,
                    "quantity": round(quantity, 2),
                    "unit_price": unit_price,
                    "total": line_total,
                    "po_reference": po["po_number"],
                    "po_line_number": po_line["line_number"]
                })
        else:
            # Fallback: use rate cards if no PO line items available
            if invoice_type == "PROFORMA" and sow_rate_cards:
                # Repeat rate cards to get enough for 100-200 items
                selected_rates = []
                for _ in range(num_items):
                    selected_rates.append(random.choice(sow_rate_cards))
            else:
                selected_rates = random.sample(sow_rate_cards, min(num_items, len(sow_rate_cards))) if sow_rate_cards else []
            
            for line_idx, rate in enumerate(selected_rates):
                # For LABOR invoices, use timesheet hours as quantity (ensures invoice hours match timesheet)
                if invoice_type == "LABOR" and timesheet_hours is not None:
                    # For first line item, use all timesheet hours; for others, use 0
                    if line_idx == 0:
                        quantity = timesheet_hours
                    else:
                        quantity = 0.0  # Additional line items have 0 hours (for multi-line LABOR invoices)
                else:
                    quantity = random.uniform(10, 50)
                
                # Rate violation: charge above rate card (if selected)
                if "rate_violation" in selected_exceptions:
                    unit_price = rate["unit_price"] * random.uniform(1.06, 1.15)  # 6-15% above
                    exception_flags["rate_violation"] = True
                else:
                    # NOT selected: use valid rate card price to prevent rate_violation
                    unit_price = rate["unit_price"]
                
                line_total = round(quantity * unit_price, 2)
                total_amount += line_total
                
                # Generate intelligent description
                description = _generate_line_item_description(
                    invoice_type,
                    rate["item_code"],
                    line_num=line_idx + 1
                )
                
                line_items.append({
                    "line_number": line_idx + 1,
                    "item_code": rate["item_code"],
                    "description": description,
                    "quantity": round(quantity, 2),
                    "unit_price": unit_price,
                    "total": line_total,
                    "po_reference": po["po_number"],
                    "po_line_number": None  # No PO line item reference available
                })
        
        # Abnormal spikes: significantly higher amount (if selected)
        # CRITICAL FIX: For abnormal_spike scenario, ensure there's sufficient historical data
        # and the spike is significant enough compared to historical patterns
        # The anomaly validator uses vendor_name and sow_number, so we need historical invoices for the same vendor/SOW
        if "abnormal_spike" in selected_exceptions:
            # Get vendor name and SOW number for historical invoice lookup
            vendor_name = vendor.get("vendor_name", "")
            sow_number = sow.get("sow_number", "")
            
            # Get historical invoice patterns for this vendor/SOW to ensure spike is significant
            # The anomaly validator queries by vendor_name and sow_number, not sow_id
            cursor.execute("""
                SELECT AVG(hi.total_amount) as avg_amount, MAX(hi.total_amount) as max_amount, COUNT(*) as count
                FROM historical_invoices hi
                JOIN vendors v ON hi.vendor_id = v.vendor_id
                JOIN statements_of_work s ON hi.sow_id = s.sow_id
                WHERE v.vendor_name = ? AND s.sow_number = ? AND hi.final_status = 'approved'
            """, (vendor_name, sow_number))
            hist_row = cursor.fetchone()
            
            if hist_row and hist_row[2] and hist_row[2] > 0:  # count is at index 2
                avg_amount = float(hist_row[0]) if hist_row[0] else 0.0  # avg_amount is at index 0
                max_amount = float(hist_row[1]) if hist_row[1] else 0.0  # max_amount is at index 1
                
                # Ensure spike is at least 1.5x the average (50% variance threshold from anomaly validator)
                # The anomaly validator uses: threshold_multiplier = 1 + (variance_percentage / 100) = 1.5 for 50% variance
                # So we need: current_amount >= average_amount * 1.5
                min_spike_amount = avg_amount * 1.5 if avg_amount > 0 else total_amount * 2.0
                if total_amount < min_spike_amount:
                    # Increase amount to ensure significant spike (at least 1.5x average, preferably 1.6-2.0x)
                    total_amount = min_spike_amount * random.uniform(1.1, 1.3)
                    # Adjust line items proportionally
                    if line_items:
                        scale_factor = total_amount / sum(item["total"] for item in line_items)
                        for item in line_items:
                            item["total"] = round(item["total"] * scale_factor, 2)
                            item["quantity"] = round(item["total"] / item["unit_price"], 2) if item["unit_price"] > 0 else item["quantity"]
            else:
                # No historical data - use a large multiplier to ensure spike is detected
                # But also ensure we don't exceed milestone cap (if wbs_budget_exceeded is NOT selected)
                if "wbs_budget_exceeded" not in selected_exceptions:
                    # Check milestone cap and stay within it
                    cursor.execute("""
                        SELECT milestone_cap_amount FROM milestones 
                        WHERE sow_id = ? AND approval_status = 'approved'
                        ORDER BY planned_date DESC LIMIT 1
                    """, (sow["sow_id"],))
                    milestone_cap_result = cursor.fetchone()
                    if milestone_cap_result and milestone_cap_result[0]:
                        milestone_cap = float(milestone_cap_result[0])
                        cursor.execute("""
                            SELECT COALESCE(SUM(total_amount), 0) as total_billed
                            FROM historical_invoices
                            WHERE sow_id = ? AND final_status = 'approved'
                        """, (sow["sow_id"],))
                        billed_row = cursor.fetchone()
                        total_billed_so_far = float(billed_row[0]) if billed_row else 0.0
                        remaining_cap = milestone_cap - total_billed_so_far
                        if remaining_cap > 0:
                            # Use 80-95% of remaining cap to create a spike but stay within cap
                            total_amount = remaining_cap * random.uniform(0.8, 0.95)
                            # Adjust line items proportionally
                            if line_items:
                                scale_factor = total_amount / sum(item["total"] for item in line_items)
                                for item in line_items:
                                    item["total"] = round(item["total"] * scale_factor, 2)
                                    item["quantity"] = round(item["total"] / item["unit_price"], 2) if item["unit_price"] > 0 else item["quantity"]
                    else:
                        # No milestone cap - use large multiplier
                        total_amount *= random.uniform(2.5, 3.5)
                        # Adjust line items proportionally
                        if line_items:
                            scale_factor = total_amount / sum(item["total"] for item in line_items)
                            for item in line_items:
                                item["total"] = round(item["total"] * scale_factor, 2)
                                item["quantity"] = round(item["total"] / item["unit_price"], 2) if item["unit_price"] > 0 else item["quantity"]
                else:
                    # wbs_budget_exceeded is also selected - will be handled in wbs_budget_exceeded section
                    # Use standard multiplier for now, milestone section will adjust if needed
                    total_amount *= random.uniform(1.5, 2.5)
                    # Adjust line items proportionally
                    if line_items:
                        scale_factor = total_amount / sum(item["total"] for item in line_items)
                        for item in line_items:
                            item["total"] = round(item["total"] * scale_factor, 2)
                            item["quantity"] = round(item["total"] / item["unit_price"], 2) if item["unit_price"] > 0 else item["quantity"]
            
            exception_flags["abnormal_spike"] = True
        else:
            # NOT selected: ensure amount is NOT abnormally high to prevent abnormal_spike
            # Get historical patterns and ensure invoice amount is within normal range
            # The anomaly validator queries by vendor_name and sow_number
            vendor_name = vendor.get("vendor_name", "")
            sow_number = sow.get("sow_number", "")
            
            cursor.execute("""
                SELECT AVG(hi.total_amount) as avg_amount, MAX(hi.total_amount) as max_amount, COUNT(*) as count
                FROM historical_invoices hi
                JOIN vendors v ON hi.vendor_id = v.vendor_id
                JOIN statements_of_work s ON hi.sow_id = s.sow_id
                WHERE v.vendor_name = ? AND s.sow_number = ? AND hi.final_status = 'approved'
            """, (vendor_name, sow_number))
            hist_row = cursor.fetchone()
            
            if hist_row and hist_row[2] and hist_row[2] > 0:  # count is at index 2
                avg_amount = float(hist_row[0]) if hist_row[0] else 0.0  # avg_amount is at index 0
                max_amount = float(hist_row[1]) if hist_row[1] else 0.0  # max_amount is at index 1
                
                # Ensure amount is within normal range (not more than 1.4x average to stay below 1.5x threshold)
                # The anomaly validator threshold is 1.5x (50% variance), so we need to stay below that
                max_normal_amount = avg_amount * 1.4 if avg_amount > 0 else total_amount
                if total_amount > max_normal_amount:
                    # CRITICAL FIX: For LABOR invoices with timesheet_hours, skip scaling to preserve timesheet_hours quantity
                    # The timesheet_hours must match the invoice quantity, so we cannot scale it down
                    # Instead, we rely on historical data having similar amounts to keep the average reasonable
                    if invoice_type == "LABOR" and timesheet_hours is not None:
                        # Skip scaling for LABOR invoices with timesheet_hours to preserve quantity
                        # This ensures invoice hours match timesheet hours for validation
                        pass
                    else:
                        # Reduce amount to stay within normal range for non-LABOR invoices
                        scale_factor = max_normal_amount / total_amount
                        for item in line_items:
                            item["quantity"] = round(item["quantity"] * scale_factor, 2)
                            item["total"] = round(item["unit_price"] * item["quantity"], 2)
                        total_amount = sum(item["total"] for item in line_items)
        
        # WBS Budget Exceeded exception (if selected)
        # Note: This was renamed from milestone_cap_exceeded to wbs_budget_exceeded
        # CRITICAL FIX: Only apply WBS budget exception if PO line items have WBS assignments
        if "wbs_budget_exceeded" in selected_exceptions:
            # Check if PO line items have WBS assignments
            cursor.execute("""
                SELECT COUNT(*) FROM po_line_items
                WHERE po_number = ? AND wbs_id IS NOT NULL
            """, (po["po_number"],))
            wbs_count = cursor.fetchone()[0]
            
            if wbs_count > 0:
                # PO line items have WBS assignments - proceed with WBS budget exception
                cursor.execute("""
                    SELECT milestone_cap_amount FROM milestones 
                    WHERE sow_id = ? AND approval_status = 'approved'
                    ORDER BY planned_date DESC LIMIT 1
                """, (sow["sow_id"],))
                milestone_result = cursor.fetchone()
                if milestone_result and milestone_result[0]:
                    milestone_cap = float(milestone_result[0])
                    # Get total already billed from historical invoices for this SOW
                    cursor.execute("""
                        SELECT COALESCE(SUM(total_amount), 0) as total_billed
                        FROM historical_invoices
                        WHERE sow_id = ? AND final_status = 'approved'
                    """, (sow["sow_id"],))
                    billed_row = cursor.fetchone()
                    total_billed_so_far = float(billed_row[0]) if billed_row else 0.0
                    
                    # Calculate what amount would exceed the cap
                    remaining_cap = milestone_cap - total_billed_so_far
                    if remaining_cap > 0 and (total_amount + total_billed_so_far) < milestone_cap:
                        # Need to increase amount to exceed cap (110-130% of remaining cap)
                        total_amount = remaining_cap * random.uniform(1.1, 1.3)
                        # Adjust line items proportionally to match new total
                        if line_items:
                            original_total = sum(item["total"] for item in line_items)
                            if original_total > 0:
                                scale_factor = total_amount / original_total
                                for item in line_items:
                                    item["total"] = round(item["total"] * scale_factor, 2)
                                    item["quantity"] = round(item["total"] / item["unit_price"], 2) if item["unit_price"] > 0 else item["quantity"]
                    # Always set the flag - invoice amount now exceeds the cap
                    exception_flags["wbs_budget_exceeded"] = True
                else:
                    # If no milestone cap found, still create the exception condition
                    # Increase amount significantly to ensure it would exceed any reasonable cap
                    # Use a multiplier that ensures it's clearly an exception
                    original_total = total_amount
                    total_amount *= random.uniform(2.5, 4.0)
                    # Adjust line items proportionally
                    if line_items:
                        scale_factor = total_amount / original_total if original_total > 0 else 1.0
                        for item in line_items:
                            item["total"] = round(item["total"] * scale_factor, 2)
                            item["quantity"] = round(item["total"] / item["unit_price"], 2) if item["unit_price"] > 0 else item["quantity"]
                    exception_flags["wbs_budget_exceeded"] = True
            else:
                # No WBS assignments on PO line items - remove this exception
                selected_exceptions.discard("wbs_budget_exceeded")
                exception_flags.pop("wbs_budget_exceeded", None)
                # Update scenario_type if needed
                if len(selected_exceptions) == 1:
                    scenario_type = list(selected_exceptions)[0]
                elif len(selected_exceptions) > 1:
                    scenario_type = "multi_factor"
                else:
                    # No exceptions left - this shouldn't happen, but handle it
                    scenario_type = "straight_through"
            
            # CRITICAL FIX: For wbs_budget_exceeded, ensure ld_not_applied is NOT triggered
            # If ld_not_applied is NOT selected, ensure milestones are NOT late
            if "ld_not_applied" not in selected_exceptions:
                # Check if there are any late milestones
                cursor.execute("""
                    SELECT milestone_id FROM milestones 
                    WHERE sow_id = ? AND actual_date IS NOT NULL AND planned_date IS NOT NULL
                        AND actual_date > planned_date
                    LIMIT 1
                """, (sow["sow_id"],))
                late_milestone = cursor.fetchone()
                if late_milestone:
                    # There's a late milestone - update it to not be late (set actual_date = planned_date)
                    cursor.execute("""
                        UPDATE milestones 
                        SET actual_date = planned_date
                        WHERE sow_id = ? AND actual_date > planned_date
                    """, (sow["sow_id"],))
        else:
            # NOT selected: ensure invoice amount does NOT exceed milestone cap
            cursor.execute("""
                SELECT milestone_cap_amount FROM milestones 
                WHERE sow_id = ? AND approval_status = 'approved'
                ORDER BY planned_date DESC LIMIT 1
            """, (sow["sow_id"],))
            milestone_result = cursor.fetchone()
            if milestone_result and milestone_result[0]:
                milestone_cap = float(milestone_result[0])
                cursor.execute("""
                    SELECT COALESCE(SUM(total_amount), 0) as total_billed
                    FROM historical_invoices
                    WHERE sow_id = ? AND final_status = 'approved'
                """, (sow["sow_id"],))
                billed_row = cursor.fetchone()
                total_billed_so_far = float(billed_row[0]) if billed_row else 0.0
                
                # Ensure invoice amount stays within milestone cap (use 60-80% of remaining cap)
                remaining_cap = milestone_cap - total_billed_so_far
                if remaining_cap > 0:
                    max_invoice_amount = remaining_cap * random.uniform(0.6, 0.8)
                    if total_amount > max_invoice_amount:
                        # Reduce invoice amount to stay within cap
                        scale_factor = max_invoice_amount / total_amount
                        for item in line_items:
                            item["quantity"] = round(item["quantity"] * scale_factor, 2)
                            item["total"] = round(item["unit_price"] * item["quantity"], 2)
                        total_amount = sum(item["total"] for item in line_items)
        
        retention_percentage = sow.get("retention_percentage", 0)
        retention_applied = True
        
        # Retention not applied exception (if selected)
        # CRITICAL FIX: Only apply retention exception to invoice types where retention is applicable
        # Retention typically doesn't apply to MATERIAL invoices
        if "retention_not_applied" in selected_exceptions:
            # Check if retention is applicable for this invoice type
            if invoice_type != "MATERIAL" and retention_percentage > 0:
                # For this exception, retention must NOT be applied even if SOW has retention_percentage
                retention_applied = False
                exception_flags["retention_not_applied"] = True
            else:
                # Retention not applicable for this invoice type or SOW doesn't have retention
                # Remove this exception
                selected_exceptions.discard("retention_not_applied")
                exception_flags.pop("retention_not_applied", None)
                # Update scenario_type if needed
                if len(selected_exceptions) == 1:
                    scenario_type = list(selected_exceptions)[0]
                elif len(selected_exceptions) > 1:
                    scenario_type = "multi_factor"
                else:
                    # No exceptions left - this shouldn't happen, but handle it
                    scenario_type = "straight_through"
        # else: retention_applied = True (already set above) - ensures retention IS applied
        
        # LD not applied exception (if selected)
        ld_applicable = sow.get("ld_applicable", False)
        ld_amount = 0
        ld_applied = True
        
        if "ld_not_applied" in selected_exceptions:
            if not ld_applicable:
                # Force LD to be applicable for this exception scenario
                ld_applicable = True
            
            # Check if milestone is late - if not, create one that's late
            cursor.execute("""
                SELECT milestone_id, planned_date, actual_date FROM milestones 
                WHERE sow_id = ? AND actual_date IS NOT NULL AND planned_date IS NOT NULL
                    AND actual_date > planned_date
                ORDER BY planned_date DESC LIMIT 1
            """, (sow["sow_id"],))
            milestone_result = cursor.fetchone()
            
            if milestone_result and milestone_result[2]:
                # Late milestone exists - use it
                planned = datetime.strptime(milestone_result[1], "%Y-%m-%d")
                actual = datetime.strptime(milestone_result[2], "%Y-%m-%d")
                days_late = (actual - planned).days
                ld_rate = sow.get("ld_rate_per_day", 1000)
                ld_amount = round(days_late * ld_rate, 2)
                ld_applied = False  # Exception: LD should be applied but isn't
                exception_flags["ld_not_applied"] = True
            else:
                # No late milestone found - create one that's late
                # Find the most recent milestone for this SOW
                cursor.execute("""
                    SELECT milestone_id, planned_date FROM milestones 
                    WHERE sow_id = ? 
                    ORDER BY planned_date DESC LIMIT 1
                """, (sow["sow_id"],))
                recent_milestone = cursor.fetchone()
                
                if recent_milestone:
                    # Update the milestone to be late
                    milestone_id = recent_milestone[0]
                    planned = datetime.strptime(recent_milestone[1], "%Y-%m-%d")
                    # Make it 5-15 days late
                    days_late = random.randint(5, 15)
                    actual = planned + timedelta(days=days_late)
                    
                    cursor.execute("""
                        UPDATE milestones 
                        SET actual_date = ?, approval_status = 'approved'
                        WHERE milestone_id = ?
                    """, (actual.strftime("%Y-%m-%d"), milestone_id))
                    
                    ld_rate = sow.get("ld_rate_per_day", 1000)
                    ld_amount = round(days_late * ld_rate, 2)
                    ld_applied = False  # Exception: LD should be applied but isn't
                    exception_flags["ld_not_applied"] = True
                else:
                    # No milestones at all - create a new one that's late
                    # This shouldn't happen if we filtered correctly, but handle it anyway
                    invoice_date_obj = datetime.strptime(invoice_date, "%Y-%m-%d")
                    planned = invoice_date_obj - timedelta(days=30)
                    days_late = random.randint(5, 15)
                    actual = planned + timedelta(days=days_late)
                    
                    milestone_id = f"MIL-{uuid.uuid4().hex[:8].upper()}"
                    cursor.execute("""
                        INSERT INTO milestones 
                        (milestone_id, milestone_code, project_id, sow_id, milestone_name,
                         milestone_type, planned_date, actual_date, approval_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (milestone_id, f"MS-{sow['sow_number']}-LD", sow["project_id"], 
                          sow["sow_id"], "LD Exception Milestone", "completion",
                          planned.strftime("%Y-%m-%d"), actual.strftime("%Y-%m-%d"), "approved"))
                    
                    ld_rate = sow.get("ld_rate_per_day", 1000)
                    ld_amount = round(days_late * ld_rate, 2)
                    ld_applied = False
                    exception_flags["ld_not_applied"] = True
            
            # CRITICAL FIX: For ld_not_applied, ensure wbs_budget_exceeded is NOT triggered
            # If wbs_budget_exceeded is NOT selected, ensure invoice amount doesn't exceed milestone cap
            if "wbs_budget_exceeded" not in selected_exceptions:
                cursor.execute("""
                    SELECT milestone_cap_amount FROM milestones 
                    WHERE sow_id = ? AND approval_status = 'approved'
                    ORDER BY planned_date DESC LIMIT 1
                """, (sow["sow_id"],))
                milestone_cap_result = cursor.fetchone()
                if milestone_cap_result and milestone_cap_result[0]:
                    milestone_cap = float(milestone_cap_result[0])
                    # Get total already billed from historical invoices for this SOW
                    cursor.execute("""
                        SELECT COALESCE(SUM(total_amount), 0) as total_billed
                        FROM historical_invoices
                        WHERE sow_id = ? AND final_status = 'approved'
                    """, (sow["sow_id"],))
                    billed_row = cursor.fetchone()
                    total_billed_so_far = float(billed_row[0]) if billed_row else 0.0
                    
                    # Ensure invoice amount stays within milestone cap (use 60-80% of remaining cap)
                    remaining_cap = milestone_cap - total_billed_so_far
                    if remaining_cap > 0:
                        max_invoice_amount = remaining_cap * random.uniform(0.6, 0.8)
                        if total_amount > max_invoice_amount:
                            # Reduce invoice amount to stay within cap
                            # Adjust line items proportionally
                            scale_factor = max_invoice_amount / total_amount
                            for item in line_items:
                                item["quantity"] = round(item["quantity"] * scale_factor, 2)
                                item["total"] = round(item["unit_price"] * item["quantity"], 2)
                            total_amount = sum(item["total"] for item in line_items)
        else:
            # NOT selected: ensure LD IS applied (if applicable) to prevent ld_not_applied
            if ld_applicable:
                # Check if milestone is late
                cursor.execute("""
                    SELECT milestone_id, planned_date, actual_date FROM milestones 
                    WHERE sow_id = ? AND actual_date IS NOT NULL AND planned_date IS NOT NULL
                        AND actual_date > planned_date
                    ORDER BY planned_date DESC LIMIT 1
                """, (sow["sow_id"],))
                milestone_result = cursor.fetchone()
                
                if milestone_result and milestone_result[2]:
                    # Late milestone exists - calculate and apply LD
                    planned = datetime.strptime(milestone_result[1], "%Y-%m-%d")
                    actual = datetime.strptime(milestone_result[2], "%Y-%m-%d")
                    days_late = (actual - planned).days
                    ld_rate = sow.get("ld_rate_per_day", 1000)
                    ld_amount = round(days_late * ld_rate, 2)
                    ld_applied = True  # LD IS applied (not an exception)
                else:
                    # No late milestones - LD not applicable
                    ld_applicable = False
                    ld_applied = True
                    ld_amount = 0
            else:
                # LD not applicable for this SOW
                ld_applied = True
                ld_amount = 0
        
        # Missing evidence exception (if selected)
        # Only include evidence references if evidence actually exists
        # If evidence is missing, don't mention it in the invoice at all
        evidence_references = []
        if "missing_evidence" in selected_exceptions:
            # Evidence is missing - don't include any references in invoice
            # The missing evidence will be detected during validation, not mentioned in invoice
            evidence_references = []
            exception_flags["missing_evidence"] = True
            
            # CRITICAL FIX: Ensure all line items use valid rate cards to prevent rate_violation
            # (since rate_violation is NOT selected)
            if "rate_violation" not in selected_exceptions:
                # Verify all line items have matching rate cards
                for item in line_items:
                    item_code = item.get("item_code", "")
                    matching_rate = next((rc for rc in sow_rate_cards if rc.get("item_code") == item_code), None)
                    if not matching_rate:
                        # If no matching rate card, use a rate card from the SOW (any one)
                        if sow_rate_cards:
                            matching_rate = random.choice(sow_rate_cards)
                            item["item_code"] = matching_rate["item_code"]
                            item["description"] = matching_rate.get("description", "Service Item")
                            # Use rate card price to ensure no rate violation
                            item["unit_price"] = matching_rate["unit_price"]
                            item["total"] = round(item["quantity"] * item["unit_price"], 2)
                
                # Recalculate total after any adjustments
                total_amount = sum(item["total"] for item in line_items)
        else:
            # NOT selected: Evidence exists - include evidence references based on invoice type
            # Get invoice type from SOW
            invoice_type = sow.get("invoice_type", "PROFORMA")
            evidence_references = _get_evidence_references_for_invoice_type(invoice_type, invoice_number)
        
        # CRITICAL: Ensure ALL selected exceptions are in exception_flags
        # This is the final safety check - set any missing exception flags
        # Some exceptions might have been set conditionally above, but we need ALL selected ones
        for exc in selected_exceptions:
            if exc not in exception_flags:
                exception_flags[exc] = True
        
        # Verify all selected exceptions are in exception_flags
        if len(exception_flags) < len(selected_exceptions):
            # This shouldn't happen, but log a warning
            missing = selected_exceptions - set(exception_flags.keys())
            print(f"  ⚠ Warning: Exception flags mismatch for invoice {invoice_number}. Missing: {missing}")
            # Set them anyway
            for exc in missing:
                exception_flags[exc] = True
        
        # Assign language: Check SOW metadata from global memory first, then fallback to English (especially for global_memory_only)
        language = "en"  # Default to English
        sow_number = sow.get("sow_number")
        if sow_metadata_from_global and sow_number and sow_number in sow_metadata_from_global:
            # Check if SOW metadata has language field
            sow_metadata = sow_metadata_from_global[sow_number]
            if "language" in sow_metadata and sow_metadata["language"]:
                language = sow_metadata["language"]
            # If no language in metadata, default to English (don't use distribution list for global_memory_only)
        # If no SOW metadata, default to English (don't randomize for global_memory_only scenario)
        
        invoice_data = {
            "invoice_number": invoice_number,
            "vendor_name": vendor["vendor_name"],
            "invoice_date": invoice_date,
            "due_date": due_date,
            "po_reference": po["po_number"],
            "sow_reference": sow["sow_number"],
            "project_reference": project["project_code"],
            "wbs_reference": wbs["wbs_code"],
            "additional_projects": additional_projects,
            "line_items": line_items,
            "total_amount": round(total_amount, 2),
            "tax_amount": 0,
            "retention_percentage": retention_percentage,
            "retention_applied": retention_applied,
            "ld_applicable": ld_applicable,
            "ld_amount": ld_amount,
            "ld_applied": ld_applied,
            "evidence_references": _get_evidence_references_for_invoice_type(invoice_type, invoice_number)
        }
        
        # Store timesheet hours in invoice_data for evidence generation (LABOR invoices only)
        if invoice_type == "LABOR" and timesheet_hours is not None:
            invoice_data["timesheet_hours"] = timesheet_hours
        
        filepath = generate_invoice_pdf(invoices_dir, invoice_data, language=language)
        
        cursor.execute("""
            INSERT INTO incoming_invoices (invoice_id, invoice_file_path, status, document_language, submitted_at, scenario_type, exception_flags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (invoice_id, str(filepath), "pending", language, datetime.now().isoformat(), 
              scenario_type, json.dumps(exception_flags)))
        
        invoices.append({
            "invoice_id": invoice_id,
            "invoice_number": invoice_number,
            "vendor_id": vendor["vendor_id"],
            "po_number": po["po_number"],
            "sow_id": sow["sow_id"],
            "project_id": project["project_id"],
            "total_amount": invoice_data["total_amount"],
            "scenario_type": scenario_type,
            "exception_flags": exception_flags,
            "invoice_data": invoice_data,
            "document_language": language
        })
    
    # Count actual straight-through vs exception invoices based on generated data
    # Use scenario_type which is set explicitly during generation and is more reliable
    # scenario_type is "straight_through" for straight-through invoices, or exception name/"multi_factor" for exceptions
    actual_straight_through = sum(1 for inv in invoices if inv.get("scenario_type") == "straight_through")
    actual_exceptions = len(invoices) - actual_straight_through
    actual_straight_through_pct = (actual_straight_through / len(invoices) * 100) if len(invoices) > 0 else 0
    actual_exception_pct = (actual_exceptions / len(invoices) * 100) if len(invoices) > 0 else 0
    print(f"  ✓ Generated {len(invoices)} invoice PDFs ({actual_straight_through} straight-through ({actual_straight_through_pct:.0f}%), {actual_exceptions} with exceptions ({actual_exception_pct:.0f}%))")
    return invoices


def generate_timesheet_pdf(output_dir: Path, invoice_number: str, coverage_start: datetime, 
                           coverage_end: datetime, worker_name: str, hours: float, role: Optional[str] = None, language: str = "en") -> str:
    """Generate a professional timesheet PDF with format variations.
    
    Args:
        role: Role name (e.g., "Senior Engineer", "Technician") - required for validation
        language: ISO 639-1 language code (default: 'en')
    """
    filename = f"Timesheet-{invoice_number}.pdf"
    filepath = output_dir / filename
    
    templates = get_language_template(language)
    font_name = get_font_for_language(language)
    format_style = get_evidence_format_style(invoice_number)
    
    # Available width: 7"
    available_width = 7 * inch
    doc = SimpleDocTemplate(str(filepath), pagesize=letter,
                           leftMargin=0.75 * inch, rightMargin=0.75 * inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Different header styles based on format
    header_colors = {
        "standard": colors.HexColor('#2C5282'),
        "compact": colors.HexColor('#1565C0'),
        "detailed": colors.HexColor('#0D47A1'),
        "minimal": colors.HexColor('#1976D2')
    }
    header_color = header_colors.get(format_style, header_colors["standard"])
    
    if format_style == "minimal":
        # Minimal header - just text
        header_text = Paragraph(templates['timesheet'].upper(), ParagraphStyle(
            'MinimalHeader', parent=styles['Title'], fontSize=18,
            textColor=header_color, alignment=TA_CENTER, spaceAfter=10, fontName=font_name
        ))
        story.append(header_text)
        story.append(Spacer(1, 0.2 * inch))
    elif format_style == "compact":
        # Compact header - smaller bar
        header_para = Paragraph(templates['timesheet'].upper(), ParagraphStyle(
            'TimesheetHeader',
            parent=styles['Title'],
            fontSize=20,
            textColor=colors.whitesmoke,
            alignment=TA_CENTER,
            fontName=font_name
        ))
        header_bar = Table([[header_para]], colWidths=[available_width], rowHeights=[0.6 * inch])
        header_bar.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), header_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(header_bar)
        story.append(Spacer(1, 0.2 * inch))
    else:
        # Standard or detailed - full header bar
        header_para = Paragraph(templates['timesheet'].upper(), ParagraphStyle(
            'TimesheetHeader',
            parent=styles['Title'],
            fontSize=24,
            textColor=colors.whitesmoke,
            alignment=TA_CENTER,
            fontName=font_name
        ))
        header_bar = Table([[header_para]], colWidths=[available_width], rowHeights=[0.8 * inch])
        header_bar.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), header_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(header_bar)
        story.append(Spacer(1, 0.3 * inch))
    
    # Worker and period info
    # Create style for info values to support CJK fonts
    info_label_style = ParagraphStyle(
        'InfoLabel',
        parent=styles['Normal'],
        fontSize=10,
        fontName=font_name
    )
    info_value_style = ParagraphStyle(
        'InfoValue',
        parent=styles['Normal'],
        fontSize=10,
        fontName=font_name
    )
    
    # Get role label from templates, fallback to "Role:" if not available
    role_label = templates.get('role', 'Role:')
    # Use provided role or generate a random one if not provided
    if not role:
        labor_roles = ["Project Manager", "Senior Engineer", "Engineer", "Technician", "Supervisor"]
        role = random.choice(labor_roles)
    
    info_data = [
        [Paragraph(templates['worker_name'], info_label_style), Paragraph(worker_name, info_value_style)],
        [Paragraph(role_label, info_label_style), Paragraph(role, info_value_style)],
        [Paragraph(templates['employee_id'], info_label_style), Paragraph(f"EMP-{random.randint(1000, 9999)}", info_value_style)],
        [Paragraph(templates['coverage_period'], info_label_style), Paragraph(f"{coverage_start.strftime('%B %d, %Y')} to {coverage_end.strftime('%B %d, %Y')}", info_value_style)],
        [Paragraph(templates['total_hours_worked'], info_label_style), Paragraph(f"{hours:.2f} {templates['hours'].lower()}", info_value_style)],
        [Paragraph(templates['invoice_reference'], info_label_style), Paragraph(invoice_number, info_value_style)],
        [Paragraph(templates['project'], info_label_style), Paragraph(f"Project-{random.randint(100, 999)}", info_value_style)],
    ]
    
    info_table = Table(info_data, colWidths=[2.2 * inch, 4.5 * inch])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F4F8')),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Daily breakdown table with varied hours per day
    days = (coverage_end - coverage_start).days + 1
    num_entries = min(days, 7)  # Show up to 7 days
    
    # Generate varied hours per day that sum to total hours
    # Use weighted random distribution to create realistic variation
    daily_hours_list = []
    remaining_hours = hours
    remaining_days = num_entries
    
    for i in range(num_entries - 1):
        # Vary hours: 60-140% of average, but ensure we don't exceed remaining hours
        avg_hours = remaining_hours / remaining_days if remaining_days > 0 else 0
        min_hours = max(0.5, avg_hours * 0.6)  # At least 0.5 hours
        max_hours = min(remaining_hours - (remaining_days - 1) * 0.5, avg_hours * 1.4)
        
        if max_hours <= min_hours:
            day_hours = min_hours
        else:
            day_hours = random.uniform(min_hours, max_hours)
        
        daily_hours_list.append(day_hours)
        remaining_hours -= day_hours
        remaining_days -= 1
    
    # Last day gets remaining hours
    daily_hours_list.append(max(0, remaining_hours))
    
    # Shuffle to avoid pattern (optional, but adds more realism)
    if random.random() < 0.5:
        random.shuffle(daily_hours_list)
    
    # Create style for daily table values to support CJK fonts
    daily_table_header_style = ParagraphStyle(
        'DailyTableHeader',
        parent=styles['Normal'],
        fontSize=10 if format_style != "compact" else 9,
        fontName=font_name,
        textColor=colors.whitesmoke
    )
    daily_table_value_style = ParagraphStyle(
        'DailyTableValue',
        parent=styles['Normal'],
        fontSize=9 if format_style != "compact" else 8,
        fontName=font_name
    )
    
    # Build table based on format style
    if format_style == "detailed":
        # Detailed format: includes start/end times
        daily_data = [[
            Paragraph(templates['date'], daily_table_header_style),
            Paragraph(templates['start'], daily_table_header_style),
            Paragraph(templates['end'], daily_table_header_style),
            Paragraph(templates['hours'], daily_table_header_style),
            Paragraph(templates['task'], daily_table_header_style),
            Paragraph(templates['location'], daily_table_header_style)
        ]]
        current_date = coverage_start
        for i in range(num_entries):
            day_hours = daily_hours_list[i]
            start_hour = random.randint(6, 8)
            start_min = random.choice([0, 15, 30])
            end_hour = start_hour + int(day_hours) + random.randint(0, 1)
            end_min = start_min + int((day_hours % 1) * 60)
            if end_min >= 60:
                end_min -= 60
                end_hour += 1
            
            daily_data.append([
                Paragraph(current_date.strftime("%Y-%m-%d"), daily_table_value_style),
                Paragraph(f"{start_hour:02d}:{start_min:02d}", daily_table_value_style),
                Paragraph(f"{end_hour:02d}:{end_min:02d}", daily_table_value_style),
                Paragraph(f"{day_hours:.2f}", daily_table_value_style),
                Paragraph(f"Work Task {i+1}", daily_table_value_style),
                Paragraph(f"Site-{random.randint(1, 5)}", daily_table_value_style)
            ])
            current_date += timedelta(days=1)
    elif format_style == "compact":
        # Compact format: fewer columns
        daily_data = [[
            Paragraph(templates['date'], daily_table_header_style),
            Paragraph(templates['hours'], daily_table_header_style),
            Paragraph(templates['task'], daily_table_header_style)
        ]]
        current_date = coverage_start
        for i in range(num_entries):
            day_hours = daily_hours_list[i]
            daily_data.append([
                Paragraph(current_date.strftime("%m/%d"), daily_table_value_style),
                Paragraph(f"{day_hours:.1f}", daily_table_value_style),
                Paragraph(f"Task {i+1}", daily_table_value_style)
            ])
            current_date += timedelta(days=1)
    else:
        # Standard or minimal format
        daily_data = [[
            Paragraph(templates['date'], daily_table_header_style),
            Paragraph(templates['hours'], daily_table_header_style),
            Paragraph(templates['task_description'], daily_table_header_style),
            Paragraph(templates['location'], daily_table_header_style)
        ]]
        current_date = coverage_start
        for i in range(num_entries):
            day_hours = daily_hours_list[i]
            daily_data.append([
                Paragraph(current_date.strftime("%Y-%m-%d"), daily_table_value_style),
                Paragraph(f"{day_hours:.2f}", daily_table_value_style),
                Paragraph(f"Work Task {i+1}", daily_table_value_style),
                Paragraph(f"Site-{random.randint(1, 5)}", daily_table_value_style)
            ])
            current_date += timedelta(days=1)
    
    # Daily table with format-specific column widths
    if format_style == "detailed":
        # Detailed: 0.9" + 0.6" + 0.6" + 0.6" + 2.1" + 1.2" = 6.0"
        col_widths = [0.9 * inch, 0.6 * inch, 0.6 * inch, 0.6 * inch, 2.1 * inch, 1.2 * inch]
    elif format_style == "compact":
        # Compact: 1.5" + 0.8" + 3.7" = 6.0"
        col_widths = [1.5 * inch, 0.8 * inch, 3.7 * inch]
    else:
        # Standard/minimal: 1.1" + 0.7" + 2.8" + 1.4" = 6.0"
        col_widths = [1.1 * inch, 0.7 * inch, 2.8 * inch, 1.4 * inch]
    
    daily_table = Table(daily_data, colWidths=col_widths)
    
    # Format-specific styling
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ])
    
    # Center-align hours column
    hours_col_idx = 1 if format_style != "detailed" else 3
    table_style.add('ALIGN', (hours_col_idx, 1), (hours_col_idx, -1), 'CENTER')
    
    # Add row backgrounds for standard/detailed formats
    if format_style != "compact":
        table_style.add('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')])
    
    # Add alternating column backgrounds for detailed format
    if format_style == "detailed":
        table_style.add('BACKGROUND', (hours_col_idx, 1), (hours_col_idx, -1), colors.HexColor('#E3F2FD'))
    
    daily_table.setStyle(table_style)
    story.append(daily_table)
    
    # Signature section with actual signature text
    story.append(Spacer(1, 0.4 * inch))
    worker_sig = generate_signature_text(worker_name)
    supervisor_names = ["Michael Johnson", "Sarah Williams", "David Brown", "Jennifer Davis"]
    supervisor_sig = generate_signature_text(random.choice(supervisor_names))
    sig_date = coverage_end.strftime("%Y-%m-%d")
    
    # Create style for signature labels and values
    sig_label_style = ParagraphStyle(
        'SigLabel',
        parent=styles['Normal'],
        fontSize=9,
        fontName=font_name
    )
    sig_value_style = ParagraphStyle(
        'SigValue',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Oblique'  # Italic for signatures
    )
    
    signature_data = [
        [Paragraph(templates['worker_signature'], sig_label_style), Paragraph(worker_sig, sig_value_style), Paragraph(templates['date'] + ":", sig_label_style), Paragraph(sig_date, sig_value_style)],
        [Paragraph(templates['supervisor_approval'], sig_label_style), Paragraph(supervisor_sig, sig_value_style), Paragraph(templates['date'] + ":", sig_label_style), Paragraph(sig_date, sig_value_style)],
    ]
    # Signature table: 1.4" + 2.0" + 0.7" + 2.1" = 6.2" (fits in 7")
    sig_table = Table(signature_data, colWidths=[1.4 * inch, 2.0 * inch, 0.7 * inch, 2.1 * inch])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(sig_table)
    
    doc.build(story)
    return str(filepath)


def generate_completion_cert_pdf(output_dir: Path, invoice_number: str, completion_date: datetime,
                                 work_description: str, approved_by: str, milestone_reference: Optional[str] = None, language: str = "en") -> str:
    """Generate a professional completion certificate PDF with format variations.
    
    Args:
        milestone_reference: Milestone reference (e.g., "MIL-2024-001") - required for validation
        language: ISO 639-1 language code (default: 'en')
    """
    filename = f"Completion-Cert-{invoice_number}.pdf"
    filepath = output_dir / filename
    
    templates = get_language_template(language)
    font_name = get_font_for_language(language)
    format_style = get_evidence_format_style(invoice_number)
    
    # Available width: 7"
    available_width = 7 * inch
    doc = SimpleDocTemplate(str(filepath), pagesize=letter,
                           leftMargin=0.75 * inch, rightMargin=0.75 * inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Different certificate styles
    cert_colors = {
        "standard": colors.HexColor('#1B4332'),
        "compact": colors.HexColor('#2E7D32'),
        "detailed": colors.HexColor('#004D40'),
        "minimal": colors.HexColor('#388E3C')
    }
    cert_color = cert_colors.get(format_style, cert_colors["standard"])
    
    header_style = ParagraphStyle(
        'CertHeader',
        parent=styles['Title'],
        fontSize=22 if format_style != "minimal" else 18,
        textColor=cert_color,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName=font_name  # Use CJK font for Mandarin support
    )
    
    story.append(Paragraph(templates['completion_certificate'].upper(), header_style))
    
    # Decorative border (varies by format)
    border_height = 0.08 * inch if format_style == "detailed" else 0.05 * inch
    border = Table([[""]], colWidths=[available_width], rowHeights=[border_height])
    border.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), cert_color),
    ]))
    story.append(border)
    story.append(Spacer(1, 0.3 * inch))
    
    # Certificate body
    cert_text = ParagraphStyle(
        'CertText',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=15,
        fontName=font_name
    )
    
    story.append(Paragraph(templates['certify_intro'], cert_text))
    story.append(Spacer(1, 0.2 * inch))
    
    # Work description in highlighted box
    work_box = Table([[work_description]], colWidths=[available_width], rowHeights=[1 * inch])
    work_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E8F5E9')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (-1, -1), cert_color),
        ('GRID', (0, 0), (-1, -1), 2, cert_color),
    ]))
    story.append(work_box)
    
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(templates['certify_completion'], cert_text))
    story.append(Spacer(1, 0.4 * inch))
    
    # Create style for details labels and values
    details_label_style = ParagraphStyle(
        'DetailsLabel',
        parent=styles['Normal'],
        fontSize=10 if format_style != "compact" else 9,
        fontName=font_name
    )
    details_value_style = ParagraphStyle(
        'DetailsValue',
        parent=styles['Normal'],
        fontSize=10 if format_style != "compact" else 9,
        fontName=font_name
    )
    
    # Get milestone reference label from templates, fallback to "Milestone Reference:" if not available
    milestone_label = templates.get('milestone_reference', 'Milestone Reference:')
    # Use provided milestone_reference or generate one if not provided
    if not milestone_reference:
        milestone_reference = f"MIL-{random.randint(2024, 2026)}-{random.randint(100, 999)}"
    
    # Details table with format-specific fields
    if format_style == "detailed":
        # Detailed format: more fields
        details_data = [
            [Paragraph(templates['completion_date'], details_label_style), Paragraph(completion_date.strftime("%B %d, %Y"), details_value_style)],
            [Paragraph(templates['invoice_reference'], details_label_style), Paragraph(invoice_number, details_value_style)],
            [Paragraph(milestone_label, details_label_style), Paragraph(milestone_reference, details_value_style)],
            [Paragraph(templates['project_code'], details_label_style), Paragraph(f"PRJ-{random.randint(100, 999)}", details_value_style)],
            [Paragraph(templates['work_order'], details_label_style), Paragraph(f"WO-{random.randint(1000, 9999)}", details_value_style)],
            [Paragraph(templates['contract_number'], details_label_style), Paragraph(f"CNT-{random.randint(10000, 99999)}", details_value_style)],
            [Paragraph(templates['location'] + ":", details_label_style), Paragraph(f"Site-{random.randint(1, 5)}", details_value_style)],
            [Paragraph(templates['quality_check'], details_label_style), Paragraph(templates['passed'], details_value_style)],
            [Paragraph(templates['safety_compliance'], details_label_style), Paragraph(templates['verified'], details_value_style)],
        ]
    elif format_style == "compact":
        # Compact format: fewer fields, single line
        details_data = [
            [Paragraph(templates['date'] + ":", details_label_style), Paragraph(completion_date.strftime("%m/%d/%Y"), details_value_style), Paragraph(templates['invoice_number'] + ":", details_label_style), Paragraph(invoice_number, details_value_style)],
            [Paragraph(milestone_label, details_label_style), Paragraph(milestone_reference, details_value_style), Paragraph(templates['project'], details_label_style), Paragraph(f"PRJ-{random.randint(100, 999)}", details_value_style)],
            [Paragraph("WO:", details_label_style), Paragraph(f"WO-{random.randint(1000, 9999)}", details_value_style), Paragraph("", details_label_style), Paragraph("", details_value_style)],
        ]
    else:
        # Standard or minimal format
        details_data = [
            [Paragraph(templates['completion_date'], details_label_style), Paragraph(completion_date.strftime("%B %d, %Y"), details_value_style)],
            [Paragraph(templates['invoice_reference'], details_label_style), Paragraph(invoice_number, details_value_style)],
            [Paragraph(milestone_label, details_label_style), Paragraph(milestone_reference, details_value_style)],
            [Paragraph(templates['project_code'], details_label_style), Paragraph(f"PRJ-{random.randint(100, 999)}", details_value_style)],
            [Paragraph(templates['work_order'], details_label_style), Paragraph(f"WO-{random.randint(1000, 9999)}", details_value_style)],
        ]
    
    # Format-specific table layout
    if format_style == "compact":
        details_table = Table(details_data, colWidths=[1.5 * inch, 2.0 * inch, 1.0 * inch, 2.5 * inch])
    else:
        details_table = Table(details_data, colWidths=[2.2 * inch, 4.5 * inch])
    
    details_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F5E9') if format_style != "compact" else colors.white),
    ]))
    story.append(details_table)
    
    # Approval section with signature
    story.append(Spacer(1, 0.5 * inch))
    approver_sig = generate_signature_text(approved_by)
    
    # Create style for approval labels and values
    approval_label_style = ParagraphStyle(
        'ApprovalLabel',
        parent=styles['Normal'],
        fontSize=10,
        fontName=font_name
    )
    approval_value_style = ParagraphStyle(
        'ApprovalValue',
        parent=styles['Normal'],
        fontSize=10,
        fontName=font_name
    )
    approval_sig_style = ParagraphStyle(
        'ApprovalSig',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Oblique'  # Italic for signature
    )
    
    approval_data = [
        [Paragraph(templates['approved_by'], approval_label_style), Paragraph(approved_by, approval_value_style), Paragraph(templates['date'] + ":", approval_label_style), Paragraph(completion_date.strftime("%Y-%m-%d"), approval_value_style)],
        [Paragraph(templates['title'], approval_label_style), Paragraph(templates['project_manager'], approval_value_style), Paragraph(templates['signature'] + ":", approval_label_style), Paragraph(approver_sig, approval_sig_style)],
    ]
    # Approval table: 1.1" + 2.0" + 0.7" + 2.4" = 6.2" (fits in 7")
    approval_table = Table(approval_data, colWidths=[1.1 * inch, 2.0 * inch, 0.7 * inch, 2.4 * inch])
    approval_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(approval_table)
    
    doc.build(story)
    return str(filepath)


def generate_grn_pdf(output_dir: Path, invoice_number: str, grn_date: datetime,
                     po_reference: Optional[str] = None, vendor_name: Optional[str] = None,
                     line_items: Optional[List[Dict[str, Any]]] = None, language: str = "en") -> str:
    """Generate a professional Goods Receipt Note (GRN) PDF with format variations.
    
    Args:
        output_dir: Directory to save PDF
        invoice_number: Invoice number for reference
        grn_date: GRN date
        po_reference: PO reference (optional)
        vendor_name: Vendor name (optional)
        line_items: List of material line items (optional, will generate if not provided)
        language: ISO 639-1 language code (default: 'en')
    """
    filename = f"GRN-{invoice_number}.pdf"
    filepath = output_dir / filename
    
    templates = get_language_template(language)
    font_name = get_font_for_language(language)
    format_style = get_evidence_format_style(invoice_number)
    
    # Available width: 7"
    available_width = 7 * inch
    doc = SimpleDocTemplate(str(filepath), pagesize=letter,
                           leftMargin=0.75 * inch, rightMargin=0.75 * inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Different warehouse/logistics header styles
    grn_colors = {
        "standard": colors.HexColor('#6A1B9A'),
        "compact": colors.HexColor('#7B1FA2'),
        "detailed": colors.HexColor('#4A148C'),
        "minimal": colors.HexColor('#8E24AA')
    }
    grn_color = grn_colors.get(format_style, grn_colors["standard"])
    
    # Generate GRN number
    grn_number = f"GRN-{invoice_number}"
    
    # Generate line items if not provided
    if not line_items:
        num_items = random.randint(2, 5)
        line_items = []
        material_types = ["Steel Pipe 12in", "Valve Assembly", "Flange Set", "Gasket Kit", "Bolt Set"]
        units = ["pieces", "kg", "meters", "sets", "units"]
        for i in range(num_items):
            material_code = f"MAT-{random.randint(1000, 9999)}"
            description = random.choice(material_types)
            quantity = round(random.uniform(10, 500), 2)
            unit = random.choice(units)
            line_items.append({
                "item_number": f"{i+1:03d}",
                "material_code": material_code,
                "description": description,
                "quantity": quantity,
                "unit_of_measure": unit
            })
    
    if format_style == "minimal":
        header_text = Paragraph(templates.get('grn', 'Goods Receipt Note').upper(), ParagraphStyle(
            'MinimalHeader', parent=styles['Title'], fontSize=16,
            textColor=grn_color, alignment=TA_CENTER, spaceAfter=10, fontName=font_name
        ))
        story.append(header_text)
        story.append(Spacer(1, 0.2 * inch))
    else:
        header_height = 0.6 * inch if format_style == "compact" else 0.8 * inch
        header_para = Paragraph(templates.get('grn', 'Goods Receipt Note').upper(), ParagraphStyle(
            'GRNHeader',
            parent=styles['Title'],
            fontSize=20 if format_style != "compact" else 18,
            textColor=colors.whitesmoke,
            alignment=TA_CENTER,
            fontName=font_name
        ))
        header_bar = Table([[header_para]], colWidths=[available_width], rowHeights=[header_height])
        header_bar.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), grn_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(header_bar)
        story.append(Spacer(1, 0.3 * inch))
    
    # Create style for GRN info labels and values
    grn_label_style = ParagraphStyle(
        'GRNLabel',
        parent=styles['Normal'],
        fontSize=10,
        fontName=font_name
    )
    grn_value_style = ParagraphStyle(
        'GRNValue',
        parent=styles['Normal'],
        fontSize=10,
        fontName=font_name
    )
    
    # GRN information
    delivery_date = grn_date - timedelta(days=random.randint(0, 3))
    grn_data = [
        [Paragraph(templates.get('grn_number', 'GRN Number:'), grn_label_style), Paragraph(grn_number, grn_value_style)],
        [Paragraph(templates.get('grn_date', 'GRN Date:'), grn_label_style), Paragraph(grn_date.strftime("%B %d, %Y"), grn_value_style)],
        [Paragraph(templates.get('delivery_date', 'Delivery Date:'), grn_label_style), Paragraph(delivery_date.strftime("%B %d, %Y"), grn_value_style)],
    ]
    
    if po_reference:
        grn_data.append([Paragraph(templates.get('po_reference', 'PO Reference:'), grn_label_style), Paragraph(po_reference, grn_value_style)])
    if vendor_name:
        grn_data.append([Paragraph(templates.get('vendor', 'Vendor:'), grn_label_style), Paragraph(vendor_name, grn_value_style)])
    grn_data.append([Paragraph(templates.get('invoice_reference', 'Invoice Reference:'), grn_label_style), Paragraph(invoice_number, grn_value_style)])
    
    grn_table = Table(grn_data, colWidths=[2.2 * inch, 4.5 * inch])
    grn_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F3E5F5')),
    ]))
    story.append(grn_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Create style for line items table headers and values
    items_table_header_style = ParagraphStyle(
        'ItemsTableHeader',
        parent=styles['Normal'],
        fontSize=10 if format_style != "compact" else 9,
        fontName=font_name,
        textColor=colors.whitesmoke
    )
    items_table_value_style = ParagraphStyle(
        'ItemsTableValue',
        parent=styles['Normal'],
        fontSize=9 if format_style != "compact" else 8,
        fontName=font_name
    )
    
    # Line items table
    if format_style == "detailed":
        items_entries = [[
            Paragraph(templates.get('item_code', 'Item Code'), items_table_header_style),
            Paragraph(templates.get('material_description', 'Material Description'), items_table_header_style),
            Paragraph(templates.get('quantity', 'Quantity'), items_table_header_style),
            Paragraph(templates.get('unit_of_measure', 'Unit'), items_table_header_style),
            Paragraph(templates.get('status', 'Status'), items_table_header_style)
        ]]
        for item in line_items:
            items_entries.append([
                Paragraph(item.get('material_code', ''), items_table_value_style),
                Paragraph(item.get('description', ''), items_table_value_style),
                Paragraph(str(item.get('quantity', 0)), items_table_value_style),
                Paragraph(item.get('unit_of_measure', ''), items_table_value_style),
                Paragraph("Received", items_table_value_style)
            ])
        col_widths = [1.0 * inch, 2.5 * inch, 0.8 * inch, 0.9 * inch, 1.8 * inch]
    elif format_style == "compact":
        items_entries = [[
            Paragraph(templates.get('item_code', 'Item Code'), items_table_header_style),
            Paragraph(templates.get('material_description', 'Description'), items_table_header_style),
            Paragraph(templates.get('quantity', 'Qty'), items_table_header_style),
            Paragraph(templates.get('unit_of_measure', 'Unit'), items_table_header_style)
        ]]
        for item in line_items:
            items_entries.append([
                Paragraph(item.get('material_code', ''), items_table_value_style),
                Paragraph(item.get('description', ''), items_table_value_style),
                Paragraph(str(item.get('quantity', 0)), items_table_value_style),
                Paragraph(item.get('unit_of_measure', ''), items_table_value_style)
            ])
        col_widths = [1.0 * inch, 2.5 * inch, 1.0 * inch, 1.5 * inch]
    else:
        items_entries = [[
            Paragraph(templates.get('item_code', 'Item Code'), items_table_header_style),
            Paragraph(templates.get('material_description', 'Description'), items_table_header_style),
            Paragraph(templates.get('quantity', 'Quantity'), items_table_header_style),
            Paragraph(templates.get('unit_of_measure', 'Unit'), items_table_header_style)
        ]]
        for item in line_items:
            items_entries.append([
                Paragraph(item.get('material_code', ''), items_table_value_style),
                Paragraph(item.get('description', ''), items_table_value_style),
                Paragraph(str(item.get('quantity', 0)), items_table_value_style),
                Paragraph(item.get('unit_of_measure', ''), items_table_value_style)
            ])
        col_widths = [1.2 * inch, 2.8 * inch, 1.0 * inch, 1.0 * inch]
    
    items_table = Table(items_entries, colWidths=col_widths)
    
    # Format-specific styling
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grn_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),  # Right-align quantity column
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ])
    
    # Add row backgrounds for standard/detailed formats
    if format_style != "compact":
        table_style.add('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')])
    
    items_table.setStyle(table_style)
    story.append(items_table)
    
    # Receipt confirmation section
    story.append(Spacer(1, 0.4 * inch))
    received_by_names = ["Sarah Johnson", "Michael Chen", "David Brown", "Lisa Anderson"]
    received_by = random.choice(received_by_names)
    received_sig = generate_signature_text(received_by)
    
    # Create style for receipt labels and values
    receipt_label_style = ParagraphStyle(
        'ReceiptLabel',
        parent=styles['Normal'],
        fontSize=10,
        fontName=font_name
    )
    receipt_value_style = ParagraphStyle(
        'ReceiptValue',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Oblique'  # Italic for signature
    )
    
    receipt_data = [
        [Paragraph(templates.get('received_by', 'Received By:'), receipt_label_style), Paragraph(received_by, receipt_value_style), Paragraph(templates.get('date', 'Date') + ":", receipt_label_style), Paragraph(grn_date.strftime("%Y-%m-%d"), receipt_value_style)],
        [Paragraph(templates.get('receipt_confirmed', 'Receipt Confirmed'), receipt_label_style), Paragraph(received_sig, receipt_value_style), Paragraph("", receipt_label_style), Paragraph("", receipt_value_style)],
    ]
    # Receipt table: 1.8" + 2.4" + 0.7" + 1.1" = 6.0" (fits in 7")
    receipt_table = Table(receipt_data, colWidths=[1.8 * inch, 2.4 * inch, 0.7 * inch, 1.1 * inch])
    receipt_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(receipt_table)
    
    doc.build(story)
    return str(filepath)


def generate_evidence_pdfs(cursor, invoices: List[Dict[str, Any]], output_dir: Path) -> List[Dict[str, Any]]:
    """Generate evidence PDFs (timesheets, completion certs, GRN) based on invoice type."""
    if not REPORTLAB_AVAILABLE:
        print("  ⚠ Skipping PDF generation (reportlab not available)")
        return []
    
    evidence_dir = output_dir / "evidence"
    evidence_types_dirs = {
        "timesheet": evidence_dir / "timesheets",
        "completion_certificate": evidence_dir / "completion_certs",
        "grn": evidence_dir / "grn"
    }
    
    for subdir in evidence_types_dirs.values():
        subdir.mkdir(parents=True, exist_ok=True)
    
    evidence_docs = []
    
    for invoice in invoices:
        invoice_id = invoice["invoice_id"]
        invoice_number = invoice["invoice_number"]
        invoice_data = invoice.get("invoice_data", {})
        scenario_type = invoice.get("scenario_type", "straight_through")
        exception_flags = invoice.get("exception_flags", {})
        language = invoice.get("document_language", "en")
        
        # Determine invoice type from invoice number or SOW
        invoice_type = None
        if invoice_number.startswith("INV-LABOR-"):
            invoice_type = "LABOR"
        elif invoice_number.startswith("INV-MATERIAL-"):
            invoice_type = "MATERIAL"
        elif invoice_number.startswith("INV-PROFORMA-"):
            invoice_type = "PROFORMA"
        else:
            # Fallback: try to determine from SOW
            sow_ref = invoice_data.get('sow_reference')
            if sow_ref:
                # Query SOW to get invoice_type
                cursor.execute("""
                    SELECT invoice_type FROM statements_of_work WHERE sow_number = ?
                """, (sow_ref,))
                sow_row = cursor.fetchone()
                if sow_row and sow_row[0]:
                    invoice_type = sow_row[0]
        
        # Determine required evidence types based on invoice type
        evidence_types_map = {
            "LABOR": ["timesheet"],
            "MATERIAL": ["grn"],
            "PROFORMA": ["timesheet", "completion_certificate", "grn"]
        }
        required_evidence_types = evidence_types_map.get(invoice_type, ["timesheet", "completion_certificate", "grn"])
        
        # Missing evidence exception: generate fewer than required
        missing_evidence = exception_flags.get("missing_evidence", False)
        if missing_evidence:
            # For missing_evidence exception, ensure at least one required evidence type is missing
            # Generate 0 to (required_count - 1) evidence files to guarantee missing evidence
            # For LABOR (1 required): generate 0 (always missing)
            # For MATERIAL (1 required): generate 0 (always missing)
            # For PROFORMA (3 required): generate 0-2 (always at least 1 missing)
            num_to_generate = random.randint(0, max(0, len(required_evidence_types) - 1))
            selected_types = random.sample(required_evidence_types, min(num_to_generate, len(required_evidence_types))) if num_to_generate > 0 else []
        else:
            # Normal scenario: generate all required evidence types
            selected_types = required_evidence_types
        
        invoice_date = datetime.strptime(invoice_data["invoice_date"], "%Y-%m-%d")
        
        for evid_type in selected_types:
            evidence_id = f"EVID-{uuid.uuid4().hex[:8].upper()}"
            filepath = None
            
            if evid_type == "timesheet":
                coverage_start = invoice_date - timedelta(days=random.randint(1, 7))
                coverage_end = invoice_date
                worker_name = f"Worker-{random.randint(100, 999)}"
                # Use timesheet hours from invoice_data if available (for LABOR invoices, this ensures hours match invoice quantity)
                hours = invoice_data.get("timesheet_hours", random.uniform(40, 80))
                # Extract role from invoice line items (for LABOR invoices, line items have role)
                role = None
                if invoice_data.get('line_items'):
                    # Find first line item with a role (LABOR invoices should have roles)
                    for item in invoice_data['line_items']:
                        if item.get('role'):
                            role = item['role']
                            break
                filepath = generate_timesheet_pdf(
                    evidence_types_dirs[evid_type], invoice_number, coverage_start, coverage_end, worker_name, hours, role=role, language=language
                )
            
            elif evid_type == "completion_certificate":
                completion_date = invoice_date - timedelta(days=random.randint(0, 5))
                sow_ref = invoice_data.get('sow_reference', 'N/A')
                templates = get_language_template(language)
                work_desc = templates['work_completed_per_sow'].format(sow_reference=sow_ref)
                approved_by = f"Approver-{random.randint(1, 10)}"
                # Extract milestone_reference from invoice data if available
                milestone_reference = invoice_data.get('milestone_reference') or invoice_data.get('milestone_id')
                filepath = generate_completion_cert_pdf(
                    evidence_types_dirs[evid_type], invoice_number, completion_date, work_desc, approved_by, milestone_reference=milestone_reference, language=language
                )
            
            elif evid_type == "grn":
                grn_date = invoice_date - timedelta(days=random.randint(0, 3))
                po_ref = invoice_data.get('po_reference')
                vendor_name = invoice_data.get('vendor_name')
                # Use invoice line items if available, otherwise generate
                line_items_data = None
                if invoice_data.get('line_items'):
                    line_items_data = []
                    for item in invoice_data['line_items']:
                        line_items_data.append({
                            "item_number": str(item.get('line_number', '')),
                            "material_code": item.get('item_code', ''),
                            "description": item.get('description', ''),
                            "quantity": item.get('quantity', 0),
                            "unit_of_measure": item.get('unit', 'pieces')
                        })
                filepath = generate_grn_pdf(
                    evidence_types_dirs[evid_type], invoice_number, grn_date,
                    po_reference=po_ref, vendor_name=vendor_name,
                    line_items=line_items_data, language=language
                )
            
            if filepath:
                cursor.execute("""
                    INSERT INTO evidence_documents 
                    (evidence_id, invoice_id, evidence_file_path, evidence_type, document_language, submitted_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (evidence_id, invoice_id, str(filepath), evid_type, language, datetime.now().isoformat()))
                
                evidence_docs.append({
                    "evidence_id": evidence_id,
                    "invoice_id": invoice_id,
                    "evidence_type": evid_type,
                    "file_path": filepath
                })
    
    print(f"  ✓ Generated {len(evidence_docs)} evidence PDFs")
    return evidence_docs


def analyze_invoice_validation(cursor, db_path: str, evidence_base_dir: Path) -> None:
    """Analyze invoices and generate validation report showing straight-through vs exception cases.
    
    This function analyzes all invoices in the database and generates a markdown table
    showing which invoices should go straight-through vs which require exception handling,
    with detailed explanations for each.
    """
    print("\n9. Analyzing invoice validation...")
    
    evidence_dir = evidence_base_dir / "evidence"
    
    # Get all invoices with exception metadata
    cursor.execute("""
        SELECT 
            i.invoice_id,
            i.invoice_file_path,
            i.status,
            i.document_language,
            i.scenario_type,
            i.exception_flags
        FROM incoming_invoices i
        ORDER BY i.invoice_id
    """)
    
    invoice_rows = cursor.fetchall()
    
    if not invoice_rows:
        print("  ⚠ No invoices found for analysis")
        return
    
    analyses = []
    
    for row in invoice_rows:
        invoice_id = row[0]
        invoice_file = row[1] or ""
        document_language = row[3] or "en"  # Default to English if not set
        scenario_type = row[4] if len(row) > 4 else None
        exception_flags_json = row[5] if len(row) > 5 else "{}"
        
        # Parse exception flags from JSON
        try:
            exception_flags = json.loads(exception_flags_json) if exception_flags_json else {}
        except (json.JSONDecodeError, TypeError):
            exception_flags = {}
        
        # Analyze based on invoice data and evidence to determine expected status
        # Start with exceptions from exception_flags (from generation)
        expected_exceptions = []
        
        # Add exceptions from exception_flags (these are the intended exceptions)
        if exception_flags:
            for exc_type, is_set in exception_flags.items():
                if is_set and exc_type not in expected_exceptions:
                    expected_exceptions.append(exc_type)
        
        # Get evidence for this invoice
        cursor.execute("""
            SELECT evidence_id, evidence_file_path, evidence_type
            FROM evidence_documents
            WHERE invoice_id = ?
        """, (invoice_id,))
        evidence_rows = cursor.fetchall()
        
        # Check if evidence files exist and determine required evidence based on invoice type
        missing_evidence = []
        evidence_count = len(evidence_rows)
        
        # Determine invoice type first (needed to know what evidence is required)
        invoice_type = "UNKNOWN"
        invoice_number = invoice_id
        if invoice_file:
            # Detect invoice type from filename pattern
            if "INV-LABOR-" in invoice_file:
                invoice_type = "LABOR"
            elif "INV-MATERIAL-" in invoice_file:
                invoice_type = "MATERIAL"
            elif "INV-PROFORMA-" in invoice_file:
                invoice_type = "PROFORMA"
        
        # Determine required evidence types based on invoice type
        evidence_types_map = {
            "LABOR": ["timesheet"],
            "MATERIAL": ["grn"],
            "PROFORMA": ["timesheet", "completion_certificate", "grn"]
        }
        required_evidence_types = evidence_types_map.get(invoice_type, [])
        
        # Check which evidence files exist
        found_evidence_types = []
        for evid_row in evidence_rows:
            evid_file = evid_row[1]
            evid_type = evid_row[2] or ""
            if evid_file:
                # Try to find file
                file_path = Path(evid_file)
                if not file_path.is_absolute():
                    # Try relative to evidence dir
                    type_dirs = {
                        "timesheet": "timesheets",
                        "completion_certificate": "completion_certs",
                        "grn": "grn"
                    }
                    subdir = type_dirs.get(evid_type, "")
                    if subdir:
                        filename = Path(evid_file).name
                        file_path = evidence_dir / subdir / filename
                
                if file_path.exists():
                    found_evidence_types.append(evid_type)
                else:
                    missing_evidence.append(evid_type)
        
        # Check if required evidence is missing - only add "missing_evidence" once
        has_missing_evidence = False
        for req_type in required_evidence_types:
            if req_type not in found_evidence_types:
                missing_evidence.append(req_type)
                has_missing_evidence = True
        
        if has_missing_evidence:
            if "missing_evidence" not in expected_exceptions:
                expected_exceptions.append("missing_evidence")
        
        # Determine processing path based on scenario_type (source of truth from generation)
        # scenario_type is set during generation and is the authoritative source
        # Priority: scenario_type > exception_flags > missing evidence check
        if scenario_type:
            if scenario_type == "straight_through":
                # Explicitly marked as straight-through during generation
                processing_path = "straight_through"
                # Clear any exceptions that might have been added from evidence check
                # (straight-through invoices should have all evidence)
                expected_exceptions = []
            else:
                # scenario_type indicates an exception (single exception name or "multi_factor")
                processing_path = "exception"
                # For multi_factor, expected_exceptions should already be populated from exception_flags
                # For single exception types, add scenario_type to expected_exceptions if not already there
                if scenario_type != "multi_factor" and scenario_type not in expected_exceptions:
                    expected_exceptions.insert(0, scenario_type)
        else:
            # No scenario_type (backward compatibility or data issue)
            # Fall back to checking expected_exceptions
            processing_path = "straight_through" if len(expected_exceptions) == 0 else "exception"
        
        # Extract invoice number and detect invoice type
        invoice_number = invoice_id
        invoice_type = "UNKNOWN"
        if invoice_file:
            # Updated pattern to match new format: INV-LABOR-2026-5000, INV-MATERIAL-2026-5000, INV-PROFORMA-2026-5000
            match = re.search(r'(INV-(?:LABOR|MATERIAL|PROFORMA)-\d{4}-\d{4})', invoice_file)
            if match:
                invoice_number = match.group(1)
            
            # Detect invoice type from filename pattern
            if "INV-LABOR-" in invoice_file:
                invoice_type = "LABOR"
            elif "INV-MATERIAL-" in invoice_file:
                invoice_type = "MATERIAL"
            elif "INV-PROFORMA-" in invoice_file:
                invoice_type = "PROFORMA"
            else:
                # Try to detect from invoice number if filename doesn't have pattern
                if invoice_number.startswith("INV-LABOR-"):
                    invoice_type = "LABOR"
                elif invoice_number.startswith("INV-MATERIAL-"):
                    invoice_type = "MATERIAL"
                elif invoice_number.startswith("INV-PROFORMA-"):
                    invoice_type = "PROFORMA"
        
        # Get language name from code
        language_name = SUPPORTED_LANGUAGES.get(document_language, document_language.upper())
        language_display = language_name
        
        analyses.append({
            "invoice_number": invoice_number,
            "invoice_type": invoice_type,
            "processing_path": processing_path,
            "expected_exceptions": ", ".join(expected_exceptions) if expected_exceptions else "None",
            "evidence_count": evidence_count,
            "language": language_display
        })
    
    # Generate and print table using Rich if available, otherwise fallback to markdown
    total = len(analyses)
    straight_through = len([a for a in analyses if a["processing_path"] == "straight_through"])
    exceptions = total - straight_through
    
    # Sort by processing path (straight-through first) then randomly (don't sort by invoice number)
    # This ensures the display order doesn't reveal which invoice number is straight-through
    sorted_analyses = sorted(analyses, key=lambda x: (
        0 if x["processing_path"] == "straight_through" else 1
    ))
    # Shuffle within each group to randomize display order
    straight_through_items = [a for a in sorted_analyses if a["processing_path"] == "straight_through"]
    exception_items = [a for a in sorted_analyses if a["processing_path"] != "straight_through"]
    random.shuffle(straight_through_items)
    random.shuffle(exception_items)
    sorted_analyses = straight_through_items + exception_items
    
    if RICH_AVAILABLE:
        console = Console()
        
        # Summary panel
        summary_text = f"Total Invoices: {total} | Straight-Through: {straight_through} | Exceptions: {exceptions}"
        console.print()
        console.print(Panel.fit(
            summary_text,
            title="[bold blue]Invoice Validation Analysis[/bold blue]",
            border_style="blue"
        ))
        console.print()
        
        # Create Rich table
        table = RichTable(
            title="[bold]Invoice Processing Classification[/bold]",
            show_header=True,
            header_style="bold magenta",
            border_style="blue",
            box=box.ROUNDED,
            show_lines=True
        )
        
        table.add_column("Invoice Number", style="cyan", no_wrap=False, width=25)
        table.add_column("Invoice Type", style="bright_cyan", width=12)
        table.add_column("Processing Path", style="yellow", width=18)
        table.add_column("Expected Exceptions", style="red", width=30)
        table.add_column("Evidence Count", style="blue", justify="center", width=14)
        table.add_column("Language", style="magenta", width=18)
        
        for analysis in sorted_analyses:
            invoice_num = analysis["invoice_number"]
            invoice_type = analysis["invoice_type"]
            processing_path = analysis["processing_path"].replace("_", "-").title()
            expected_exceptions = analysis["expected_exceptions"]
            evidence_count = str(analysis["evidence_count"])
            language = analysis["language"]
            
            # Color code processing path
            path_style = "green" if processing_path == "Straight-Through" else "red"
            
            # Color code invoice type
            type_style = "cyan" if invoice_type != "UNKNOWN" else "dim"
            
            table.add_row(
                invoice_num,
                f"[{type_style}]{invoice_type}[/{type_style}]",
                f"[{path_style}]{processing_path}[/{path_style}]",
                expected_exceptions if expected_exceptions != "None" else "[dim]None[/dim]",
                evidence_count,
                language
            )
        
        console.print(table)
        console.print()
    else:
        # Fallback to markdown table if Rich is not available
        print("\n" + "=" * 80)
        print("INVOICE VALIDATION ANALYSIS")
        print("=" * 80)
        print(f"\nSummary:")
        print(f"  Total Invoices: {total}")
        print(f"  Straight-Through Eligible: {straight_through}")
        print(f"  Exception Cases: {exceptions}")
        print()
        print("Invoice Processing Classification:")
        print()
        print("| Invoice Number | Invoice Type | Processing Path | Expected Exceptions | Evidence Count | Language |")
        print("|----------------|--------------|-----------------|---------------------|----------------|----------|")
        
        for analysis in sorted_analyses:
            invoice_num = analysis["invoice_number"]
            invoice_type = analysis["invoice_type"]
            processing_path = analysis["processing_path"].replace("_", "-").title()
            expected_exceptions = analysis["expected_exceptions"]
            evidence_count = analysis["evidence_count"]
            language = analysis["language"]
            
            print(f"| {invoice_num} | {invoice_type} | {processing_path} | {expected_exceptions} | "
                  f"{evidence_count} | {language} |")
        
        print()
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Setup Aegis database and mock data")
    parser.add_argument("--db-path", default="projects/pa/data/aegis/aegis_database.db",
                       help="Path to SQLite database file")
    parser.add_argument("--output-dir", default="projects/pa/data/aegis",
                       help="Base directory for generated files")
    parser.add_argument("--reset", action="store_true", default=True,
                       help="Reset database (delete existing and recreate) (default: True)")
    parser.add_argument("--no-reset", dest="reset", action="store_false",
                       help="Do not reset database (keep existing data)")
    parser.add_argument("--vendor-count", type=int, default=12,
                       help="Number of vendors to generate (default: 12)")
    parser.add_argument("--project-count", type=int, default=6,
                       help="Number of projects to generate (default: 6)")
    parser.add_argument("--po-count", type=int, default=25,
                       help="Number of POs to generate (default: 25)")
    parser.add_argument("--sow-count", type=int, default=20,
                       help="Number of SOWs to generate (default: 20)")
    parser.add_argument("--historical-invoice-count", type=int, default=125,
                       help="Number of historical invoices to generate (default: 125)")
    parser.add_argument("--current-invoice-count", type=int, default=5,
                       help="Number of current invoices to generate (default: 5)")
    parser.add_argument("--exception-percentage", type=float, default=0.8,
                       help="Percentage of invoices that should have exceptions (0.0-1.0, default: 0.8 = 80%%)")
    parser.add_argument("--non-english-pct", type=float, default=0.60,
                       help="Percentage of invoices that should be non-English (0.0-1.0, default: 0.60 = 60%%)")
    parser.add_argument("--required-non-english-language", type=str, default=None,
                       help="Force at least one non-English invoice to use this language (e.g., 'zh' for Mandarin). If not specified, all non-English languages are randomly distributed.")
    parser.add_argument("--seed", type=int, default=None,
                       help="Random seed for reproducibility (default: None = use current time for randomization)")
    parser.add_argument("--invoice-type-dist", type=str, default="LABOR:0.4,MATERIAL:0.4,PROFORMA:0.2",
                       help="Invoice type distribution as 'LABOR:weight1,MATERIAL:weight2,PROFORMA:weight3' (default: LABOR:0.4,MATERIAL:0.4,PROFORMA:0.2)")
    parser.add_argument("--global-memory-only", action="store_true", default=True,
                       help="Only generate data (SOWs, invoices) for SOWs found in global memory (default: True)")
    parser.add_argument("--no-global-memory-only", dest="global_memory_only", action="store_false",
                       help="Allow generating data for SOWs not in global memory (fallback to random generation)")
    
    args = parser.parse_args()
    
    # Parse invoice type distribution
    invoice_type_dist = None
    if args.invoice_type_dist:
        try:
            invoice_type_dist = {}
            for part in args.invoice_type_dist.split(','):
                key, value = part.split(':')
                invoice_type_dist[key.strip()] = float(value.strip())
        except (ValueError, AttributeError) as e:
            print(f"  ⚠ Warning: Invalid invoice-type-dist format '{args.invoice_type_dist}'. Using default (40% Labor, 40% Material, 20% Proforma)")
            invoice_type_dist = {"LABOR": 0.4, "MATERIAL": 0.4, "PROFORMA": 0.2}
    
    # Set random seed for reproducibility (if provided)
    # If not provided, use current time to ensure different results each run
    if args.seed is not None:
        random.seed(args.seed)
    else:
        import time
        random.seed(int(time.time()))
    
    # Detect project name for path resolution
    project_name = detect_project_name(Path.cwd())
    
    # Resolve paths intelligently
    db_path = resolve_script_path(args.db_path, project_name=project_name)
    output_dir = resolve_script_path(args.output_dir, project_name=project_name)
    
    # Reset database and output folder if requested
    if args.reset:
        if db_path.exists():
            db_path.unlink()
            print(f"✓ Removed existing database: {db_path}")
        
        if output_dir.exists():
            shutil.rmtree(output_dir)
            print(f"✓ Removed existing output directory: {output_dir}")
    
    # Create directories
    db_path.parent.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create invoice and evidence subdirectories
    invoices_dir = output_dir / "invoices" / "pending"
    evidence_dir = output_dir / "evidence"
    for subdir in ["timesheets", "completion_certs", "grn"]:
        (evidence_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 70)
    print("Aegis Database Setup")
    print("=" * 70)
    print(f"\nDatabase: {db_path}")
    print(f"Output directory: {output_dir}")
    print(f"Reset mode: {args.reset}")
    print(f"Random seed: {args.seed}")
    print()
    
    # Create database and schema
    print("1. Creating database schema...")
    create_database_schema(str(db_path))
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check for global memory SOW terms and metadata
    print("\n2. Checking global memory for SOW terms...")
    project_dir = db_path.parent.parent.parent  # Go up from data/aegis/aegis_database.db to project root
    sow_terms_from_global = read_sow_terms_from_global_memory(project_dir)
    sow_metadata_from_global = read_sow_metadata_from_global_memory(project_dir)
    
    if sow_terms_from_global:
        sow_numbers = list(sow_terms_from_global.keys())
        print(f"  ✓ Found {len(sow_numbers)} SOW(s) in global memory: {', '.join(sow_numbers)}")
        print(f"  → Will use SOW terms from global memory for data generation")
        if args.global_memory_only:
            print(f"  → global_memory_only=True: Only generating data for these SOWs")
    else:
        print(f"  ⚠ No SOW terms found in global memory")
        if args.global_memory_only:
            print(f"  ⚠ Error: global_memory_only=True but no SOWs found in global memory. Cannot generate data.")
            print(f"  → Please run Covenant pipeline first to generate SOWs in global memory, or use --no-global-memory-only")
            return
        else:
            print(f"  → Will generate all data randomly")
    
    # Phase 1.2: Foundation Data Generation
    print("\n3. Generating foundation data...")
    vendors = generate_mock_vendors(cursor, args.vendor_count)
    projects = generate_mock_projects(cursor, args.project_count)
    wbs_list = generate_mock_wbs(cursor, projects)
    
    # Phase 1.3: Contractual Data Generation
    print("\n4. Generating contractual data...")
    # Generate SOWs first (before POs, so POs can link to SOWs)
    sows, sow_global_memory_usage = generate_mock_sows(cursor, vendors, projects, args.sow_count, invoice_type_dist, sow_terms_from_global, sow_metadata_from_global, args.global_memory_only)
    # Generate POs linked to SOWs
    pos = generate_mock_pos(cursor, vendors, projects, wbs_list, sows, args.po_count)
    milestones, milestone_global_memory_usage = generate_mock_milestones(cursor, sows, projects, sow_terms_from_global)
    rate_cards = generate_mock_rate_cards(cursor, vendors, sows)
    evidence_reqs = generate_mock_evidence_requirements(cursor, sows)
    
    conn.commit()
    
    # Phase 1.4: Policy & Controls
    print("\n5. Generating policy & controls...")
    generate_anomaly_thresholds(cursor, vendors)
    
    conn.commit()
    
    # Phase 1.5: Historical Data Generation
    print("\n6. Generating historical data...")
    generate_historical_invoices(cursor, vendors, pos, sows, args.historical_invoice_count)
    
    conn.commit()
    
    # Phase 1.6: Current Invoice PDF Generation
    print("\n7. Generating current invoice PDFs...")
    # Validate exception_percentage
    if not 0.0 <= args.exception_percentage <= 1.0:
        print(f"  ⚠ Warning: exception_percentage must be between 0.0 and 1.0. Using default 0.8")
        args.exception_percentage = 0.8
    
    # Validate non_english_pct
    if not 0.0 <= args.non_english_pct <= 1.0:
        print(f"  ⚠ Warning: non-english-pct must be between 0.0 and 1.0. Using default 0.60")
        args.non_english_pct = 0.60
    
    # Reuse project_dir that was already calculated in step 2 (for reading global memory)
    # project_dir is already set from: db_path.parent.parent.parent (goes up from data/aegis/aegis_database.db to project root)
    # This ensures consistency - if we found SOWs in step 2, we'll find them again here
    
    invoices = generate_current_invoice_pdfs(cursor, vendors, pos, sows, projects, wbs_list, rate_cards, 
                                             output_dir, args.current_invoice_count, args.exception_percentage,
                                             args.non_english_pct, args.required_non_english_language, invoice_type_dist,
                                             project_dir=project_dir, global_memory_only=args.global_memory_only)
    
    # Phase 1.7: Evidence PDF Generation
    print("\n8. Generating evidence PDFs...")
    evidence_docs = generate_evidence_pdfs(cursor, invoices, output_dir)
    
    conn.commit()
    
    # Phase 1.8: Invoice Validation Analysis
    analyze_invoice_validation(cursor, str(db_path), output_dir)
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("Setup Complete!")
    print("=" * 70)
    print(f"\nDatabase: {db_path}")
    print(f"Output files: {output_dir}")
    print("\nYou can now run the Aegis pipeline!")


if __name__ == "__main__":
    main()
