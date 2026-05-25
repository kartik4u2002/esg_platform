"""
Management command to seed demo data for the ESG platform.

Creates an organization, users, data sources, import batches with
realistic raw records (including deliberate dirty data), and runs
the full pipeline synchronously so the review queue is populated.

Usage: python manage.py seed_demo_data
"""
import uuid
from datetime import date, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.tenancy.models import Organization, User
from apps.ingestion.models import DataSource, ImportBatch, RawRecord
from apps.ingestion.adapters.base import compute_checksum


class Command(BaseCommand):
    help = 'Seed demo data: org, users, sources, batches, records, and run pipeline'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Seeding demo data...'))

        # Clean existing demo data
        try:
            old_org = Organization.objects.filter(slug='acme-corp').first()
            if old_org:
                self.stdout.write('Cleaning existing Acme Corp data...')
                # Delete in reverse dependency order
                from apps.audit.models import AuditEvent, AuditLock
                from apps.review.models import ReviewDecision
                from apps.pipeline.models import NormalizedRecord, ValidationFlag
                AuditEvent.objects.filter(organization=old_org).delete()
                AuditLock.objects.filter(
                    normalized_record__organization=old_org
                ).delete()
                ReviewDecision.objects.filter(
                    normalized_record__organization=old_org
                ).delete()
                ValidationFlag.objects.filter(
                    normalized_record__organization=old_org
                ).delete()
                NormalizedRecord.objects.filter(organization=old_org).delete()
                RawRecord.objects.filter(organization=old_org).delete()
                ImportBatch.objects.filter(organization=old_org).delete()
                DataSource.objects.filter(organization=old_org).delete()
                User.objects.filter(organization=old_org).delete()
                old_org.delete()
                self.stdout.write(self.style.SUCCESS('Cleaned existing data.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Cleanup warning: {e}'))

        # 1. Create Organization
        org = Organization.objects.create(
            name='Acme Corp',
            slug='acme-corp',
            is_active=True,
        )
        self.stdout.write(f'Created organization: {org.name}')

        # 2. Create Users
        admin_user = User.objects.create_user(
            username='admin@acme.com',
            email='admin@acme.com',
            password='admin123',
            organization=org,
            role='admin',
            first_name='Admin',
            last_name='User',
        )
        analyst_user = User.objects.create_user(
            username='analyst@acme.com',
            email='analyst@acme.com',
            password='analyst123',
            organization=org,
            role='analyst',
            first_name='Analyst',
            last_name='User',
        )
        reviewer_user = User.objects.create_user(
            username='reviewer@acme.com',
            email='reviewer@acme.com',
            password='reviewer123',
            organization=org,
            role='reviewer',
            first_name='Reviewer',
            last_name='User',
        )
        self.stdout.write(f'Created 3 users: admin, analyst, reviewer')

        # 3. Create DataSources
        sap_source = DataSource.objects.create(
            organization=org,
            source_type='sap_procurement',
            scope_category='scope1',
            name='SAP Procurement Feed',
            is_active=True,
        )
        utility_source = DataSource.objects.create(
            organization=org,
            source_type='utility_electricity',
            scope_category='scope2',
            name='Utility Electricity Bills',
            is_active=True,
        )
        travel_source = DataSource.objects.create(
            organization=org,
            source_type='corporate_travel',
            scope_category='scope3',
            name='Corporate Travel System',
            is_active=True,
        )
        self.stdout.write(f'Created 3 data sources')

        # 4. Create Import Batches and Raw Records
        sap_batch = self._create_sap_batch(org, sap_source, analyst_user)
        utility_batch = self._create_utility_batch(org, utility_source, analyst_user)
        travel_batch = self._create_travel_batch(org, travel_source, analyst_user)

        # 5. Run pipeline synchronously
        self.stdout.write(self.style.NOTICE('Running pipeline...'))
        self._run_pipeline(sap_batch)
        self._run_pipeline(utility_batch)
        self._run_pipeline(travel_batch)

        self.stdout.write(self.style.SUCCESS(
            '\n✅ Demo data seeded successfully!\n'
            '\nCredentials:\n'
            '  admin@acme.com / admin123\n'
            '  analyst@acme.com / analyst123\n'
            '  reviewer@acme.com / reviewer123\n'
        ))

    def _create_sap_batch(self, org, source, user):
        """Create SAP procurement batch with 20 records including dirty data."""
        batch = ImportBatch.objects.create(
            organization=org,
            source=source,
            status='pending',
            ingested_by=user,
            file_name='sap_procurement_q1_2024.csv',
        )

        sap_records = [
            # Valid records with mixed units and date formats
            {'invoice_number': 'INV-001', 'company_code': 'CC01', 'plant_code': 'P100', 'material_number': 'MAT001', 'quantity': '150.5', 'unit': 'L', 'amount': '2500.00', 'posting_date': '15.03.2024', 'vendor_id': 'V001', 'fuel_type': 'Diesel'},
            {'invoice_number': 'INV-002', 'company_code': 'CC01', 'plant_code': 'P100', 'material_number': 'MAT002', 'quantity': '75', 'unit': 'GAL', 'amount': '3200.00', 'posting_date': '2024-03-18', 'vendor_id': 'V002', 'fuel_type': 'Gasoline'},
            {'invoice_number': 'INV-003', 'company_code': 'CC02', 'plant_code': 'P200', 'material_number': 'MAT003', 'quantity': '500', 'unit': 'KG', 'amount': '1800.00', 'posting_date': '03/20/2024', 'vendor_id': 'V003', 'fuel_type': 'LPG'},
            {'invoice_number': 'INV-004', 'company_code': 'CC01', 'plant_code': 'P100', 'material_number': 'MAT001', 'quantity': '200', 'unit': 'L', 'amount': '3100.00', 'posting_date': '22.03.2024', 'vendor_id': 'V001', 'fuel_type': 'Diesel'},
            {'invoice_number': 'INV-005', 'company_code': 'CC02', 'plant_code': 'P200', 'material_number': 'MAT004', 'quantity': '120', 'unit': 'GAL', 'amount': '4500.00', 'posting_date': '2024-03-25', 'vendor_id': 'V004', 'fuel_type': 'Gasoline'},
            {'invoice_number': 'INV-006', 'company_code': 'CC01', 'plant_code': 'P300', 'material_number': 'MAT005', 'quantity': '300', 'unit': 'KG', 'amount': '1200.00', 'posting_date': '28.03.2024', 'vendor_id': 'V005', 'fuel_type': 'Natural Gas'},
            {'invoice_number': 'INV-007', 'company_code': 'CC03', 'plant_code': 'P100', 'material_number': 'MAT001', 'quantity': '180', 'unit': 'L', 'amount': '2800.00', 'posting_date': '01.04.2024', 'vendor_id': 'V001', 'fuel_type': 'Diesel'},
            {'invoice_number': 'INV-008', 'company_code': 'CC01', 'plant_code': 'P200', 'material_number': 'MAT006', 'quantity': '90', 'unit': 'GAL', 'amount': '3800.00', 'posting_date': '2024-04-05', 'vendor_id': 'V006', 'fuel_type': 'Aviation Fuel'},
            {'invoice_number': 'INV-009', 'company_code': 'CC02', 'plant_code': 'P300', 'material_number': 'MAT003', 'quantity': '450', 'unit': 'KG', 'amount': '1600.00', 'posting_date': '04/08/2024', 'vendor_id': 'V003', 'fuel_type': 'LPG'},
            {'invoice_number': 'INV-010', 'company_code': 'CC01', 'plant_code': 'P100', 'material_number': 'MAT007', 'quantity': '220', 'unit': 'L', 'amount': '3400.00', 'posting_date': '10.04.2024', 'vendor_id': 'V007', 'fuel_type': 'Diesel'},
            {'invoice_number': 'INV-011', 'company_code': 'CC03', 'plant_code': 'P200', 'material_number': 'MAT002', 'quantity': '65', 'unit': 'GAL', 'amount': '2700.00', 'posting_date': '2024-04-12', 'vendor_id': 'V002', 'fuel_type': 'Gasoline'},
            {'invoice_number': 'INV-012', 'company_code': 'CC01', 'plant_code': 'P300', 'material_number': 'MAT008', 'quantity': '380', 'unit': 'KG', 'amount': '1400.00', 'posting_date': '15.04.2024', 'vendor_id': 'V008', 'fuel_type': 'Propane'},
            {'invoice_number': 'INV-013', 'company_code': 'CC02', 'plant_code': 'P100', 'material_number': 'MAT001', 'quantity': '195', 'unit': 'L', 'amount': '3050.00', 'posting_date': '04/18/2024', 'vendor_id': 'V001', 'fuel_type': 'Diesel'},
            {'invoice_number': 'INV-014', 'company_code': 'CC01', 'plant_code': 'P200', 'material_number': 'MAT009', 'quantity': '110', 'unit': 'GAL', 'amount': '4200.00', 'posting_date': '2024-04-22', 'vendor_id': 'V009', 'fuel_type': 'Jet Fuel'},
            {'invoice_number': 'INV-015', 'company_code': 'CC03', 'plant_code': 'P300', 'material_number': 'MAT003', 'quantity': '520', 'unit': 'KG', 'amount': '1900.00', 'posting_date': '25.04.2024', 'vendor_id': 'V003', 'fuel_type': 'LPG'},
            # DIRTY DATA: Duplicate invoices (same invoice_number + company_code)
            {'invoice_number': 'INV-001', 'company_code': 'CC01', 'plant_code': 'P100', 'material_number': 'MAT001', 'quantity': '150.5', 'unit': 'L', 'amount': '2500.00', 'posting_date': '15.03.2024', 'vendor_id': 'V001', 'fuel_type': 'Diesel'},
            {'invoice_number': 'INV-002', 'company_code': 'CC01', 'plant_code': 'P100', 'material_number': 'MAT002', 'quantity': '75', 'unit': 'GAL', 'amount': '3200.00', 'posting_date': '2024-03-18', 'vendor_id': 'V002', 'fuel_type': 'Gasoline'},
            # DIRTY DATA: Negative quantity
            {'invoice_number': 'INV-016', 'company_code': 'CC01', 'plant_code': 'P100', 'material_number': 'MAT010', 'quantity': '-50', 'unit': 'L', 'amount': '800.00', 'posting_date': '28.04.2024', 'vendor_id': 'V010', 'fuel_type': 'Diesel'},
            # DIRTY DATA: Unsupported unit
            {'invoice_number': 'INV-017', 'company_code': 'CC02', 'plant_code': 'P200', 'material_number': 'MAT011', 'quantity': '100', 'unit': 'BBL', 'amount': '5000.00', 'posting_date': '30.04.2024', 'vendor_id': 'V011', 'fuel_type': 'Crude Oil'},
            # DIRTY DATA: Invalid date
            {'invoice_number': 'INV-018', 'company_code': 'CC01', 'plant_code': 'P300', 'material_number': 'MAT012', 'quantity': '250', 'unit': 'KG', 'amount': '950.00', 'posting_date': '32.13.2024', 'vendor_id': 'V012', 'fuel_type': 'Coal'},
        ]

        self._create_raw_records(batch, org, sap_records)
        self.stdout.write(f'  Created SAP batch with {len(sap_records)} records')
        return batch

    def _create_utility_batch(self, org, source, user):
        """Create utility electricity batch with 20 records including dirty data."""
        batch = ImportBatch.objects.create(
            organization=org,
            source=source,
            status='pending',
            ingested_by=user,
            file_name='utility_electricity_q1_2024.csv',
        )

        base_date = date(2024, 1, 1)
        utility_records = []

        # Normal records for various meters (~500 kWh each)
        meters = ['MTR-001', 'MTR-002', 'MTR-003', 'MTR-004']
        for i in range(16):
            meter = meters[i % len(meters)]
            start = base_date + timedelta(days=i * 15)
            end = start + timedelta(days=14)
            utility_records.append({
                'meter_id': meter,
                'billing_start': start.strftime('%Y-%m-%d'),
                'billing_end': end.strftime('%Y-%m-%d'),
                'usage': str(450 + (i * 10) % 100),
                'unit': 'kWh',
                'tariff': '0.12',
                'facility_id': f'FAC-{(i % 4) + 1:03d}',
                'anomaly_label': '',
            })

        # DIRTY DATA: Negative usage
        utility_records.append({
            'meter_id': 'MTR-001',
            'billing_start': '2024-07-01',
            'billing_end': '2024-07-15',
            'usage': '-200',
            'unit': 'kWh',
            'tariff': '0.12',
            'facility_id': 'FAC-001',
            'anomaly_label': '',
        })

        # DIRTY DATA: Overlapping billing period (same meter, overlapping dates)
        utility_records.append({
            'meter_id': 'MTR-001',
            'billing_start': '2024-01-05',
            'billing_end': '2024-01-20',
            'usage': '480',
            'unit': 'kWh',
            'tariff': '0.12',
            'facility_id': 'FAC-001',
            'anomaly_label': '',
        })

        # DIRTY DATA: Consumption spike (10x average)
        utility_records.append({
            'meter_id': 'MTR-002',
            'billing_start': '2024-08-01',
            'billing_end': '2024-08-15',
            'usage': '5000',
            'unit': 'kWh',
            'tariff': '0.12',
            'facility_id': 'FAC-002',
            'anomaly_label': 'spike',
        })

        # DIRTY DATA: Missing tariff
        utility_records.append({
            'meter_id': 'MTR-003',
            'billing_start': '2024-08-01',
            'billing_end': '2024-08-15',
            'usage': '520',
            'unit': 'MWh',
            'tariff': '',
            'facility_id': 'FAC-003',
            'anomaly_label': '',
        })

        self._create_raw_records(batch, org, utility_records)
        self.stdout.write(f'  Created Utility batch with {len(utility_records)} records')
        return batch

    def _create_travel_batch(self, org, source, user):
        """Create corporate travel batch with 20 records including dirty data."""
        batch = ImportBatch.objects.create(
            organization=org,
            source=source,
            status='pending',
            ingested_by=user,
            file_name='travel_feed_q1_2024.json',
        )

        travel_records = [
            {'trip_id': 'TRP-001', 'employee_id': 'EMP-101', 'booking_source': 'Concur', 'from_airport': 'JFK', 'to_airport': 'LAX', 'trip_type': 'round_trip', 'travel_class': 'economy', 'hotel_type': 'standard', 'distance_km': '3983', 'transportation_cost': '450.00'},
            {'trip_id': 'TRP-002', 'employee_id': 'EMP-102', 'booking_source': 'Navan', 'from_airport': 'SFO', 'to_airport': 'ORD', 'trip_type': 'one_way', 'travel_class': 'business', 'hotel_type': 'premium', 'distance_km': '2960', 'transportation_cost': '890.00'},
            {'trip_id': 'TRP-003', 'employee_id': 'EMP-103', 'booking_source': 'Concur', 'from_airport': 'LHR', 'to_airport': 'CDG', 'trip_type': 'round_trip', 'travel_class': 'economy', 'hotel_type': 'standard', 'distance_km': '340', 'transportation_cost': '220.00'},
            {'trip_id': 'TRP-004', 'employee_id': 'EMP-104', 'booking_source': 'Direct', 'from_airport': 'DXB', 'to_airport': 'SIN', 'trip_type': 'one_way', 'travel_class': 'first', 'hotel_type': 'luxury', 'distance_km': '5848', 'transportation_cost': '2200.00'},
            {'trip_id': 'TRP-005', 'employee_id': 'EMP-105', 'booking_source': 'Concur', 'from_airport': 'FRA', 'to_airport': 'JFK', 'trip_type': 'round_trip', 'travel_class': 'business', 'hotel_type': 'premium', 'distance_km': '6200', 'transportation_cost': '1800.00'},
            {'trip_id': 'TRP-006', 'employee_id': 'EMP-101', 'booking_source': 'Navan', 'from_airport': 'LAX', 'to_airport': 'SEA', 'trip_type': 'one_way', 'travel_class': 'economy', 'hotel_type': 'budget', 'distance_km': '1535', 'transportation_cost': '180.00'},
            {'trip_id': 'TRP-007', 'employee_id': 'EMP-106', 'booking_source': 'Concur', 'from_airport': 'NRT', 'to_airport': 'ICN', 'trip_type': 'round_trip', 'travel_class': 'economy', 'hotel_type': 'standard', 'distance_km': '1200', 'transportation_cost': '350.00'},
            {'trip_id': 'TRP-008', 'employee_id': 'EMP-107', 'booking_source': 'Direct', 'from_airport': 'AMS', 'to_airport': 'BCN', 'trip_type': 'one_way', 'travel_class': 'business', 'hotel_type': 'premium', 'distance_km': '1235', 'transportation_cost': '520.00'},
            {'trip_id': 'TRP-009', 'employee_id': 'EMP-108', 'booking_source': 'Concur', 'from_airport': 'SYD', 'to_airport': 'HKG', 'trip_type': 'round_trip', 'travel_class': 'economy', 'hotel_type': 'standard', 'distance_km': '7393', 'transportation_cost': '950.00'},
            {'trip_id': 'TRP-010', 'employee_id': 'EMP-109', 'booking_source': 'Navan', 'from_airport': 'MIA', 'to_airport': 'ATL', 'trip_type': 'one_way', 'travel_class': 'economy', 'hotel_type': 'budget', 'distance_km': '970', 'transportation_cost': '150.00'},
            {'trip_id': 'TRP-011', 'employee_id': 'EMP-110', 'booking_source': 'Concur', 'from_airport': 'BOS', 'to_airport': 'DEN', 'trip_type': 'round_trip', 'travel_class': 'business', 'hotel_type': 'premium', 'distance_km': '2845', 'transportation_cost': '780.00'},
            {'trip_id': 'TRP-012', 'employee_id': 'EMP-102', 'booking_source': 'Direct', 'from_airport': 'ORD', 'to_airport': 'DFW', 'trip_type': 'one_way', 'travel_class': 'economy', 'hotel_type': 'standard', 'distance_km': '1290', 'transportation_cost': '210.00'},
            {'trip_id': 'TRP-013', 'employee_id': 'EMP-103', 'booking_source': 'Concur', 'from_airport': 'CDG', 'to_airport': 'FCO', 'trip_type': 'round_trip', 'travel_class': 'economy', 'hotel_type': 'standard', 'distance_km': '1105', 'transportation_cost': '280.00'},
            {'trip_id': 'TRP-014', 'employee_id': 'EMP-111', 'booking_source': 'Navan', 'from_airport': 'PEK', 'to_airport': 'PVG', 'trip_type': 'one_way', 'travel_class': 'business', 'hotel_type': 'luxury', 'distance_km': '1075', 'transportation_cost': '420.00'},
            {'trip_id': 'TRP-015', 'employee_id': 'EMP-112', 'booking_source': 'Concur', 'from_airport': 'IST', 'to_airport': 'MUC', 'trip_type': 'round_trip', 'travel_class': 'economy', 'hotel_type': 'standard', 'distance_km': '1850', 'transportation_cost': '390.00'},
            {'trip_id': 'TRP-016', 'employee_id': 'EMP-113', 'booking_source': 'Direct', 'from_airport': 'DEL', 'to_airport': 'BOM', 'trip_type': 'one_way', 'travel_class': 'economy', 'hotel_type': 'budget', 'distance_km': '1148', 'transportation_cost': '95.00'},
            # DIRTY DATA: Missing distance_km (3 records)
            {'trip_id': 'TRP-017', 'employee_id': 'EMP-114', 'booking_source': 'Concur', 'from_airport': 'LAX', 'to_airport': 'NRT', 'trip_type': 'round_trip', 'travel_class': 'business', 'hotel_type': 'premium', 'distance_km': None, 'transportation_cost': '2100.00'},
            {'trip_id': 'TRP-018', 'employee_id': 'EMP-115', 'booking_source': 'Navan', 'from_airport': 'JFK', 'to_airport': 'LHR', 'trip_type': 'one_way', 'travel_class': 'first', 'hotel_type': 'luxury', 'distance_km': None, 'transportation_cost': '3500.00'},
            {'trip_id': 'TRP-019', 'employee_id': 'EMP-101', 'booking_source': 'Direct', 'from_airport': 'SFO', 'to_airport': 'HND', 'trip_type': 'round_trip', 'travel_class': 'economy', 'hotel_type': 'standard', 'distance_km': None, 'transportation_cost': '1200.00'},
            # DIRTY DATA: Invalid IATA code
            {'trip_id': 'TRP-020', 'employee_id': 'EMP-116', 'booking_source': 'Concur', 'from_airport': 'ZZZ', 'to_airport': 'LAX', 'trip_type': 'one_way', 'travel_class': 'economy', 'hotel_type': 'standard', 'distance_km': '500', 'transportation_cost': '180.00'},
        ]

        self._create_raw_records(batch, org, travel_records)
        self.stdout.write(f'  Created Travel batch with {len(travel_records)} records')
        return batch

    def _create_raw_records(self, batch, org, records):
        """Create RawRecord objects from a list of payload dicts."""
        raw_records = []
        seen_checksums = set()
        for i, payload in enumerate(records):
            checksum = compute_checksum(payload)
            # Handle duplicates within batch by appending row number
            unique_checksum = checksum
            if unique_checksum in seen_checksums:
                unique_checksum = compute_checksum({**payload, '_row': i + 1})
            seen_checksums.add(unique_checksum)

            raw_records.append(RawRecord(
                batch=batch,
                organization=org,
                raw_payload=payload,
                checksum=unique_checksum,
                source_row_number=i + 1,
                pipeline_status='ingested',
            ))

        RawRecord.objects.bulk_create(raw_records)
        batch.total_rows = len(raw_records)
        batch.save(update_fields=['total_rows'])

    def _run_pipeline(self, batch):
        """Run the pipeline synchronously for all records in a batch."""
        from apps.pipeline.tasks import (
            validate_record,
            normalize_record,
            detect_anomalies,
            enqueue_for_review,
        )

        batch.status = 'processing'
        batch.save(update_fields=['status'])

        records = batch.raw_records.all()
        for record in records:
            try:
                # Run each pipeline step synchronously (not via Celery)
                raw_id = str(record.id)
                raw_id = validate_record(raw_id)
                raw_id = normalize_record(raw_id)
                raw_id = detect_anomalies(raw_id)
                enqueue_for_review(raw_id)
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f'  Pipeline error for record {record.id}: {e}'
                ))

        batch.status = 'completed'
        batch.processed_rows = batch.total_rows
        batch.save(update_fields=['status', 'processed_rows'])
        self.stdout.write(f'  Pipeline completed for batch {batch.id}')
