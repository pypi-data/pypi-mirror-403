import json
from datetime import timedelta
from unittest.mock import patch

from dcim.models import Device
from dcim.models import Interface
from dcim.models import Site
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from ipam.models import IPAddress
from ipam.models import VRF
from utilities.datetime import local_now
from utilities.forms.rendering import FieldSet

from ipfabric_netbox.choices import IPFabricFilterTypeChoices
from ipfabric_netbox.choices import IPFabricSnapshotStatusModelChoices
from ipfabric_netbox.choices import IPFabricSourceStatusChoices
from ipfabric_netbox.choices import IPFabricSourceTypeChoices
from ipfabric_netbox.choices import IPFabricSyncStatusChoices
from ipfabric_netbox.forms import IPFabricFilterExpressionForm
from ipfabric_netbox.forms import IPFabricFilterForm
from ipfabric_netbox.forms import IPFabricIngestionFilterForm
from ipfabric_netbox.forms import IPFabricIngestionMergeForm
from ipfabric_netbox.forms import IPFabricRelationshipFieldForm
from ipfabric_netbox.forms import IPFabricSnapshotFilterForm
from ipfabric_netbox.forms import IPFabricSourceFilterForm
from ipfabric_netbox.forms import IPFabricSourceForm
from ipfabric_netbox.forms import IPFabricSyncForm
from ipfabric_netbox.forms import IPFabricTransformFieldForm
from ipfabric_netbox.forms import IPFabricTransformMapCloneForm
from ipfabric_netbox.forms import IPFabricTransformMapForm
from ipfabric_netbox.forms import IPFabricTransformMapGroupForm
from ipfabric_netbox.models import IPFabricEndpoint
from ipfabric_netbox.models import IPFabricFilter
from ipfabric_netbox.models import IPFabricFilterExpression
from ipfabric_netbox.models import IPFabricRelationshipField
from ipfabric_netbox.models import IPFabricSnapshot
from ipfabric_netbox.models import IPFabricSource
from ipfabric_netbox.models import IPFabricSync
from ipfabric_netbox.models import IPFabricTransformField
from ipfabric_netbox.models import IPFabricTransformMap
from ipfabric_netbox.models import IPFabricTransformMapGroup


class IPFabricSourceFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a test IPFabricSource instance for form tests
        cls.ipfabric_source = IPFabricSource.objects.create(
            name="Test IP Fabric Source",
            type=IPFabricSourceTypeChoices.LOCAL,
            url="https://test.ipfabric.local",
            status=IPFabricSourceStatusChoices.NEW,
            parameters={"auth": "test_token", "verify": True, "timeout": 30},
        )

    def test_fields_are_required(self):
        form = IPFabricSourceForm(data={})
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("name", form.errors)
        self.assertIn("type", form.errors)
        self.assertIn("url", form.errors)

    def test_fields_are_optional(self):
        form = IPFabricSourceForm(
            data={
                "name": "Test No Comments Source",
                "type": IPFabricSourceTypeChoices.REMOTE,
                "url": "https://test.ipfabric.local",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_type_must_be_defined_choice(self):
        form = IPFabricSourceForm(
            data={
                "name": "Test Source",
                "type": "invalid_type",
                "url": "https://test.ipfabric.local",
            }
        )
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("type", form.errors)
        self.assertTrue(form.errors["type"][-1].startswith("Select a valid choice."))

    def test_valid_local_source_form(self):
        form = IPFabricSourceForm(
            data={
                "name": "Test Local Source",
                "type": IPFabricSourceTypeChoices.LOCAL,
                "url": "https://test.ipfabric.local",
                "auth": "test_api_token",
                "verify": False,
                "timeout": 45,
                "description": "Test local IP Fabric source",
                "comments": "Test comments",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()

        # Check that parameters are properly stored
        self.assertEqual(instance.parameters["auth"], "test_api_token")
        self.assertEqual(instance.parameters["verify"], False)
        self.assertEqual(instance.parameters["timeout"], 45)

    def test_valid_remote_source_form(self):
        form = IPFabricSourceForm(
            data={
                "name": "Test Remote Source",
                "type": IPFabricSourceTypeChoices.REMOTE,
                "url": "https://remote.ipfabric.local",
                "timeout": 60,
                "description": "Test remote IP Fabric source",
                "comments": "Test comments",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_local_source_requires_auth_token(self):
        # Test that when type is 'local', auth field becomes required
        form = IPFabricSourceForm(
            data={
                "name": "Test Local Source",
                "type": IPFabricSourceTypeChoices.LOCAL,
                "url": "https://test.ipfabric.local",
                "verify": True,
                "timeout": 30,
            }
        )
        # Since auth is dynamically added as required for local sources
        # we need to check if the form properly handles this validation
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("auth", form.errors)

    def test_form_save_sets_status_to_new(self):
        form = IPFabricSourceForm(
            data={
                "name": "Test Save Source",
                "type": IPFabricSourceTypeChoices.LOCAL,
                "url": "https://test.ipfabric.local",
                "auth": "test_api_token",
                "verify": True,
                "timeout": 30,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.status, IPFabricSourceStatusChoices.NEW)

    def test_form_initializes_existing_parameters(self):
        # Test that form properly initializes with existing instance parameters
        form = IPFabricSourceForm(instance=self.ipfabric_source)

        # Check that the form fields are initialized with the instance's parameters
        self.assertEqual(form.fields["auth"].initial, "test_token")
        self.assertEqual(form.fields["verify"].initial, True)
        self.assertEqual(form.fields["timeout"].initial, 30)

    def test_remote_source_creates_last_snapshot(self):
        """Check that $last snapshot is created for remote sources"""

        self.assertEqual(IPFabricSnapshot.objects.count(), 0)

        form = IPFabricSourceForm(
            data={
                "name": "Test Remote Snapshot Source",
                "type": IPFabricSourceTypeChoices.REMOTE,
                "url": "https://remote.ipfabric.local",
                "timeout": 30,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()

        last_snapshot = IPFabricSnapshot.objects.filter(
            source=instance, snapshot_id="$last"
        ).first()
        self.assertIsNotNone(last_snapshot)
        self.assertEqual(last_snapshot.name, "$last")

    def test_fieldsets_for_remote_source_type(self):
        """Test that fieldsets property returns correct structure for remote source type"""
        form = IPFabricSourceForm(
            data={
                "name": "Test Remote Source",
                "type": IPFabricSourceTypeChoices.REMOTE,
                "url": "https://remote.ipfabric.local",
            }
        )

        fieldsets = form.fieldsets

        # Should have 2 fieldsets for remote type
        self.assertEqual(len(fieldsets), 2)

        # First fieldset should be for Source
        self.assertEqual(fieldsets[0].name, "Source")

        # Second fieldset should be for Parameters
        self.assertEqual(fieldsets[1].name, "Parameters")

        # Verify the remote type fieldsets match the expected structure from forms.py
        # For remote type: FieldSet("timeout", name=_("Parameters"))
        # This means the Parameters fieldset should only contain timeout field
        self.assertEqual(len(form.fieldsets), 2)
        self.assertEqual(form.fieldsets[0].name, "Source")
        self.assertEqual(form.fieldsets[1].name, "Parameters")

        # For remote sources, verify that auth and verify fields are NOT in the form
        # (they are only added for local sources in the __init__ method)
        self.assertNotIn("auth", form.fields)
        self.assertNotIn("verify", form.fields)
        # But timeout should be present for all source types
        self.assertIn("timeout", form.fields)

    def test_fieldsets_for_local_source_type(self):
        """Test that fieldsets property returns correct structure for local source type"""
        form = IPFabricSourceForm(
            data={
                "name": "Test Local Source",
                "type": IPFabricSourceTypeChoices.LOCAL,
                "url": "https://local.ipfabric.local",
                "auth": "test_token",
                "verify": True,
                "timeout": 30,
            }
        )

        fieldsets = form.fieldsets

        # Should have 2 fieldsets for local type as well
        self.assertEqual(len(fieldsets), 2)

        # First fieldset should be for Source
        self.assertEqual(fieldsets[0].name, "Source")

        # Second fieldset should be for Parameters
        self.assertEqual(fieldsets[1].name, "Parameters")

        # Verify the local type fieldsets match the expected structure from forms.py
        # For local type: FieldSet("auth", "verify", "timeout", name=_("Parameters"))
        # This means the Parameters fieldset should contain auth, verify, and timeout fields
        self.assertEqual(len(form.fieldsets), 2)
        self.assertEqual(form.fieldsets[0].name, "Source")
        self.assertEqual(form.fieldsets[1].name, "Parameters")

        # For local sources, verify that auth, verify, and timeout fields ARE in the form
        # (they are dynamically added for local sources in the __init__ method)
        self.assertIn("auth", form.fields)
        self.assertIn("verify", form.fields)
        self.assertIn("timeout", form.fields)

        # Verify that the auth field is required for local sources
        self.assertTrue(form.fields["auth"].required)
        # Verify that verify field is optional (BooleanField with required=False)
        self.assertFalse(form.fields["verify"].required)
        # Verify that timeout field is optional
        self.assertFalse(form.fields["timeout"].required)

    def test_fieldsets_with_no_source_type_set(self):
        """Test fieldsets behavior when source_type is None or not set"""
        form = IPFabricSourceForm()

        # When no source_type is set, should default to basic fieldsets (non-local behavior)
        fieldsets = form.fieldsets

        self.assertEqual(len(fieldsets), 2)
        self.assertEqual(fieldsets[0].name, "Source")
        self.assertEqual(fieldsets[1].name, "Parameters")

    def test_fieldsets_with_existing_instance_local_type(self):
        """Test fieldsets behavior with an existing local source instance"""
        form = IPFabricSourceForm(instance=self.ipfabric_source)

        fieldsets = form.fieldsets

        # Should have extended fieldsets for local type since test instance is local
        self.assertEqual(len(fieldsets), 2)
        self.assertEqual(fieldsets[1].name, "Parameters")

    def test_fieldsets_dynamic_behavior_consistency(self):
        """Test that fieldsets method consistently returns the same structure for same source_type"""
        # Test local type consistency
        form_local_1 = IPFabricSourceForm(
            data={"type": IPFabricSourceTypeChoices.LOCAL}
        )
        form_local_2 = IPFabricSourceForm(
            data={"type": IPFabricSourceTypeChoices.LOCAL}
        )

        fieldsets_1 = form_local_1.fieldsets
        fieldsets_2 = form_local_2.fieldsets

        # Both should have the same structure
        self.assertEqual(len(fieldsets_1), len(fieldsets_2))
        self.assertEqual(fieldsets_1[0].name, fieldsets_2[0].name)
        self.assertEqual(fieldsets_1[1].name, fieldsets_2[1].name)

        # Test remote type consistency
        form_remote_1 = IPFabricSourceForm(
            data={"type": IPFabricSourceTypeChoices.REMOTE}
        )
        form_remote_2 = IPFabricSourceForm(
            data={"type": IPFabricSourceTypeChoices.REMOTE}
        )

        fieldsets_remote_1 = form_remote_1.fieldsets
        fieldsets_remote_2 = form_remote_2.fieldsets

        # Both should have the same structure
        self.assertEqual(len(fieldsets_remote_1), len(fieldsets_remote_2))
        self.assertEqual(fieldsets_remote_1[0].name, fieldsets_remote_2[0].name)
        self.assertEqual(fieldsets_remote_1[1].name, fieldsets_remote_2[1].name)

    def test_fieldsets_source_type_changes_parameters_fieldset(self):
        """Test that changing source_type results in different parameters fieldset"""
        # Create forms with different source types
        form_local = IPFabricSourceForm(data={"type": IPFabricSourceTypeChoices.LOCAL})
        form_remote = IPFabricSourceForm(
            data={"type": IPFabricSourceTypeChoices.REMOTE}
        )

        fieldsets_local = form_local.fieldsets
        fieldsets_remote = form_remote.fieldsets

        # Both should have same number of fieldsets
        self.assertEqual(len(fieldsets_local), 2)
        self.assertEqual(len(fieldsets_remote), 2)

        # Both should have same Source fieldset name
        self.assertEqual(fieldsets_local[0].name, fieldsets_remote[0].name)
        self.assertEqual(fieldsets_local[0].name, "Source")

        # Both should have Parameters fieldset, but they should be different objects
        # (one with basic timeout, one with auth, verify, timeout)
        self.assertEqual(fieldsets_local[1].name, "Parameters")
        self.assertEqual(fieldsets_remote[1].name, "Parameters")

        # The fieldsets should be different objects since they contain different fields
        # We can't easily test field contents without knowing FieldSet internals,
        # but we can verify the method creates new objects as expected
        self.assertIsInstance(fieldsets_local[1], type(fieldsets_remote[1]))


class IPFabricRelationshipFieldFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = IPFabricSource.objects.create(
            name="Test Source",
            type=IPFabricSourceTypeChoices.LOCAL,
            url="https://test.ipfabric.local",
            status=IPFabricSourceStatusChoices.NEW,
        )

        cls.transform_map_group = IPFabricTransformMapGroup.objects.create(
            name="Test Group", description="Test group description"
        )

        cls.device_content_type = ContentType.objects.get_for_model(Device)
        cls.site_content_type = ContentType.objects.get_for_model(Site)

        cls.device_endpoint = IPFabricEndpoint.objects.get(
            endpoint="/inventory/devices"
        )

        cls.transform_map = IPFabricTransformMap.objects.create(
            name="Test Transform Map",
            group=cls.transform_map_group,
            source_endpoint=cls.device_endpoint,
            target_model=cls.device_content_type,
        )

    def test_fields_are_required(self):
        form = IPFabricRelationshipFieldForm(data={})
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("transform_map", form.errors)
        self.assertIn("source_model", form.errors)
        self.assertIn("target_field", form.errors)

    def test_fields_are_optional(self):
        form = IPFabricRelationshipFieldForm(
            data={
                "transform_map": self.transform_map.pk,
                "source_model": self.device_content_type.pk,
                "target_field": "site",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_relationship_field_form(self):
        # Initialize form with transform_map to set up field choices
        form = IPFabricRelationshipFieldForm(
            initial={"transform_map": self.transform_map.pk},
            data={
                "transform_map": self.transform_map.pk,
                "source_model": self.device_content_type.pk,
                "target_field": "site",
                "coalesce": True,
                "template": "{{ object.siteName }}",
            },
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_coalesce_field_defaults_to_false(self):
        # Initialize form with transform_map to set up field choices
        form = IPFabricRelationshipFieldForm(
            initial={"transform_map": self.transform_map.pk},
            data={
                "transform_map": self.transform_map.pk,
                "source_model": self.device_content_type.pk,  # Use ContentType pk instead of string
                "target_field": "site",
            },
        )
        # Since the form requires dynamic field setup, let's manually set the choices
        form.fields["target_field"].widget.choices = [("site", "Site")]
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertFalse(instance.coalesce)

    def test_form_initialization_with_existing_instance_no_data(self):
        """Test no self.data with existing instance"""
        # Create an existing IPFabricRelationshipField instance
        relationship_field = IPFabricRelationshipField.objects.create(
            transform_map=self.transform_map,
            source_model=self.device_content_type,
            target_field="site",
            coalesce=True,
        )

        # Initialize form with existing instance but no data
        form = IPFabricRelationshipFieldForm(instance=relationship_field)

        # Verify that the form sets up field choices based on the existing instance
        self.assertIsNotNone(form.fields["target_field"].widget.choices)
        self.assertEqual(form.fields["target_field"].widget.initial, "site")

    def test_form_initialization_with_initial_transform_map_no_data(self):
        """Test no self.data with initial transform_map"""
        # Initialize form with initial transform_map but no data
        form = IPFabricRelationshipFieldForm(
            initial={"transform_map": self.transform_map.pk}
        )

        # Verify that the form sets up field choices based on the transform_map
        self.assertIsNotNone(form.fields["target_field"].widget.choices)
        # Verify choices contain relation fields (excluding exclude_fields)
        target_choices = form.fields["target_field"].widget.choices
        self.assertTrue(len(target_choices) > 0)

    def test_form_initialization_without_initial_data_no_data(self):
        """Test no self.data without initial transform_map"""
        # Initialize form without initial data and no data
        form = IPFabricRelationshipFieldForm()

        # Verify that the form doesn't crash and has default field setup
        self.assertIsNotNone(form.fields["source_model"])
        self.assertIsNotNone(form.fields["target_field"])
        # Widget choices should be empty or default since no transform_map is provided
        self.assertTrue(hasattr(form.fields["target_field"], "widget"))
        self.assertTrue(hasattr(form.fields["source_model"], "widget"))


class IPFabricTransformFieldFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = IPFabricSource.objects.create(
            name="Test Source",
            type=IPFabricSourceTypeChoices.LOCAL,
            url="https://test.ipfabric.local",
            status=IPFabricSourceStatusChoices.NEW,
        )

        cls.transform_map_group = IPFabricTransformMapGroup.objects.create(
            name="Test Group", description="Test group description"
        )

        cls.device_content_type = ContentType.objects.get_for_model(Device)

        cls.device_endpoint = IPFabricEndpoint.objects.get(
            endpoint="/inventory/devices"
        )

        cls.transform_map = IPFabricTransformMap.objects.create(
            name="Test Transform Map",
            group=cls.transform_map_group,
            source_endpoint=cls.device_endpoint,
            target_model=cls.device_content_type,
        )

    def test_fields_are_required(self):
        form = IPFabricTransformFieldForm(data={})
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("source_field", form.errors)
        self.assertIn("target_field", form.errors)
        self.assertIn("transform_map", form.errors)

    def test_fields_are_optional(self):
        form = IPFabricTransformFieldForm(
            data={
                "transform_map": self.transform_map.pk,
                "source_field": "hostname",
                "target_field": "name",
            },
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_transform_field_form(self):
        # Initialize form with transform_map to set up field choices
        form = IPFabricTransformFieldForm(
            initial={"transform_map": self.transform_map.pk},
            data={
                "transform_map": self.transform_map.pk,
                "source_field": "hostname",
                "target_field": "name",
                "coalesce": True,
                "template": "{{ object.hostname }}",
            },
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_coalesce_field_defaults_to_false(self):
        # Initialize form with transform_map to set up field choices
        form = IPFabricTransformFieldForm(
            initial={"transform_map": self.transform_map.pk},
            data={
                "transform_map": self.transform_map.pk,
                "source_field": "hostname",
                "target_field": "name",
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertFalse(instance.coalesce)

    def test_form_initialization_with_existing_instance_no_data(self):
        """Test no data with existing instance"""
        # Create an existing IPFabricTransformField instance
        transform_field = IPFabricTransformField.objects.create(
            transform_map=self.transform_map,
            source_field="hostname",
            target_field="name",
            coalesce=True,
        )

        # Initialize form with existing instance but no data
        form = IPFabricTransformFieldForm(instance=transform_field)

        # Verify that the form sets up field choices based on the existing instance
        self.assertIsNotNone(form.fields["target_field"].widget.choices)
        self.assertIsNotNone(form.fields["source_field"].widget.choices)
        self.assertEqual(form.fields["target_field"].widget.initial, "name")

    def test_form_initialization_with_initial_transform_map_no_data(self):
        """Test no data with initial transform_map"""
        # Initialize form with initial transform_map but no data
        form = IPFabricTransformFieldForm(
            initial={"transform_map": self.transform_map.pk}
        )

        # Verify that the form sets up field choices based on the transform_map
        self.assertIsNotNone(form.fields["target_field"].widget.choices)
        self.assertIsNotNone(form.fields["source_field"].widget.choices)
        # Verify choices contain non-relation fields (excluding exclude_fields)
        target_choices = form.fields["target_field"].widget.choices
        self.assertTrue(len(target_choices) > 0)

    def test_form_initialization_without_initial_data_no_data(self):
        """Test no data without initial transform_map"""
        # Initialize form without initial data and no data
        form = IPFabricTransformFieldForm()

        # Verify that the form doesn't crash and has default field setup
        self.assertIsNotNone(form.fields["source_field"])
        self.assertIsNotNone(form.fields["target_field"])
        # Widget choices should be empty or default since no transform_map is provided
        self.assertTrue(hasattr(form.fields["target_field"], "widget"))
        self.assertTrue(hasattr(form.fields["source_field"], "widget"))


class IPFabricTransformMapGroupFormTestCase(TestCase):
    def test_fields_are_required(self):
        form = IPFabricTransformMapGroupForm(data={})
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("name", form.errors)

    def test_fields_are_optional(self):
        form = IPFabricTransformMapGroupForm(data={"name": "Test Group"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_transform_map_group_form(self):
        form = IPFabricTransformMapGroupForm(
            data={"name": "Test Group", "description": "Test group description"}
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.name, "Test Group")
        self.assertEqual(instance.description, "Test group description")


class IPFabricTransformMapFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.transform_map_group = IPFabricTransformMapGroup.objects.create(
            name="Test Group", description="Test group description"
        )
        cls.device_content_type = ContentType.objects.get_for_model(Device)
        cls.device_endpoint = IPFabricEndpoint.objects.get(
            endpoint="/inventory/devices"
        )

    def test_fields_are_required(self):
        form = IPFabricTransformMapForm(data={})
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("name", form.errors)
        self.assertIn("source_endpoint", form.errors)
        self.assertIn("target_model", form.errors)

    def test_group_is_optional(self):
        # Need to avoid unique_together constraint violation
        IPFabricTransformMap.objects.get(
            group=None, target_model=self.device_content_type
        ).delete()
        form = IPFabricTransformMapForm(
            data={
                "name": "Test Transform Map",
                "source_endpoint": self.device_endpoint.pk,
                "target_model": self.device_content_type.pk,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_transform_map_form(self):
        form = IPFabricTransformMapForm(
            data={
                "name": "Test Transform Map",
                "group": self.transform_map_group.pk,
                "source_endpoint": self.device_endpoint.pk,
                "target_model": self.device_content_type.pk,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.name, "Test Transform Map")
        self.assertEqual(instance.group, self.transform_map_group)

    def test_existing_instance_excludes_self_from_parents_choices(self):
        """Test that when editing an existing transform map, it excludes itself from parents choices"""
        # Create a transform map instance
        transform_map = IPFabricTransformMap.objects.create(
            name="Test Transform Map",
            group=self.transform_map_group,
            source_endpoint=self.device_endpoint,
            target_model=self.device_content_type,
        )

        # Create another transform map that could be a parent
        other_transform_map = IPFabricTransformMap.objects.create(
            name="Other Transform Map",
            group=self.transform_map_group,
            source_endpoint=self.device_endpoint,
            target_model=ContentType.objects.get_for_model(Site),
        )

        # Initialize form with the existing instance
        form = IPFabricTransformMapForm(instance=transform_map)

        # Verify that the instance itself is excluded from parents choices
        parents_queryset = form.fields["parents"].queryset
        self.assertNotIn(transform_map, parents_queryset)

        # Verify that other transform maps are still available as parent options
        self.assertIn(other_transform_map, parents_queryset)

        # Verify help text is set
        self.assertIn(
            "must be processed before this one", form.fields["parents"].help_text
        )

    def test_circular_dependency_direct(self):
        """Test that direct circular dependencies are detected (A → B, B → A)"""
        # Create two transform maps
        site_ct = ContentType.objects.get_for_model(Site)

        tm_a = IPFabricTransformMap.objects.create(
            name="Transform Map A",
            group=self.transform_map_group,
            source_endpoint=self.device_endpoint,
            target_model=self.device_content_type,
        )

        tm_b = IPFabricTransformMap.objects.create(
            name="Transform Map B",
            group=self.transform_map_group,
            source_endpoint=self.device_endpoint,
            target_model=site_ct,
        )

        # Set B as parent of A
        tm_a.parents.add(tm_b)

        # Try to set A as parent of B (should fail)
        form = IPFabricTransformMapForm(
            instance=tm_b,
            data={
                "name": tm_b.name,
                "group": self.transform_map_group.pk,
                "source_endpoint": self.device_endpoint.pk,
                "target_model": site_ct.pk,
                "parents": [tm_a.pk],
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("parents", form.errors)
        self.assertIn("circular dependency", str(form.errors["parents"]).lower())

    def test_circular_dependency_indirect(self):
        """Test that indirect circular dependencies are detected (A → B → C → A)"""
        # Create three transform maps with different content types

        site_ct = ContentType.objects.get_for_model(Site)
        vrf_ct = ContentType.objects.get_for_model(VRF)
        interface_ct = ContentType.objects.get_for_model(Interface)

        vrf_endpoint = IPFabricEndpoint.objects.get(
            endpoint="/technology/routing/vrf/detail"
        )
        interface_endpoint = IPFabricEndpoint.objects.get(
            endpoint="/inventory/interfaces"
        )
        site_endpoint = IPFabricEndpoint.objects.get(
            endpoint="/inventory/sites/overview"
        )

        tm_a = IPFabricTransformMap.objects.create(
            name="Transform Map A",
            group=self.transform_map_group,
            source_endpoint=site_endpoint,
            target_model=site_ct,
        )

        tm_b = IPFabricTransformMap.objects.create(
            name="Transform Map B",
            group=self.transform_map_group,
            source_endpoint=vrf_endpoint,
            target_model=vrf_ct,
        )

        tm_c = IPFabricTransformMap.objects.create(
            name="Transform Map C",
            group=self.transform_map_group,
            source_endpoint=interface_endpoint,
            target_model=interface_ct,
        )

        # Create chain: A → B → C
        tm_b.parents.add(tm_a)
        tm_c.parents.add(tm_b)

        # Try to add C as parent of A (completing the cycle: A → B → C → A)
        form = IPFabricTransformMapForm(
            instance=tm_a,
            data={
                "name": tm_a.name,
                "group": self.transform_map_group.pk,
                "source_endpoint": site_endpoint.pk,
                "target_model": site_ct.pk,
                "parents": [tm_c.pk],
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("parents", form.errors)
        self.assertIn("circular dependency", str(form.errors["parents"]).lower())

    def test_valid_parent_assignment_no_cycle(self):
        """Test that valid parent assignments without cycles are allowed"""
        site_ct = ContentType.objects.get_for_model(Site)
        vrf_ct = ContentType.objects.get_for_model(VRF)

        vrf_endpoint = IPFabricEndpoint.objects.get(
            endpoint="/technology/routing/vrf/detail"
        )
        site_endpoint = IPFabricEndpoint.objects.get(
            endpoint="/inventory/sites/overview"
        )

        tm_site = IPFabricTransformMap.objects.create(
            name="Site Transform Map",
            group=self.transform_map_group,
            source_endpoint=site_endpoint,
            target_model=site_ct,
        )

        tm_vrf = IPFabricTransformMap.objects.create(
            name="VRF Transform Map",
            group=self.transform_map_group,
            source_endpoint=vrf_endpoint,
            target_model=vrf_ct,
        )

        # Set Site as parent of VRF (valid - no cycle)
        form = IPFabricTransformMapForm(
            instance=tm_vrf,
            data={
                "name": tm_vrf.name,
                "group": self.transform_map_group.pk,
                "source_endpoint": vrf_endpoint.pk,
                "target_model": vrf_ct.pk,
                "parents": [tm_site.pk],
            },
        )

        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertIn(tm_site, tm_vrf.parents.all())

    def test_multiple_parents_no_cycle(self):
        """Test that multiple parents can be assigned without creating cycles"""

        site_ct = ContentType.objects.get_for_model(Site)
        vrf_ct = ContentType.objects.get_for_model(VRF)
        interface_ct = ContentType.objects.get_for_model(Interface)
        ipaddress_ct = ContentType.objects.get_for_model(IPAddress)

        vrf_endpoint = IPFabricEndpoint.objects.get(
            endpoint="/technology/routing/vrf/detail"
        )
        interface_endpoint = IPFabricEndpoint.objects.get(
            endpoint="/inventory/interfaces"
        )
        site_endpoint = IPFabricEndpoint.objects.get(
            endpoint="/inventory/sites/overview"
        )
        ipaddress_endpoint = IPFabricEndpoint.objects.get(
            endpoint="/technology/addressing/managed-ip/ipv4"
        )

        tm_site = IPFabricTransformMap.objects.create(
            name="Site Transform Map",
            group=self.transform_map_group,
            source_endpoint=site_endpoint,
            target_model=site_ct,
        )

        tm_vrf = IPFabricTransformMap.objects.create(
            name="VRF Transform Map",
            group=self.transform_map_group,
            source_endpoint=vrf_endpoint,
            target_model=vrf_ct,
        )

        tm_interface = IPFabricTransformMap.objects.create(
            name="Interface Transform Map",
            group=self.transform_map_group,
            source_endpoint=interface_endpoint,
            target_model=interface_ct,
        )

        tm_ipaddress = IPFabricTransformMap.objects.create(
            name="IP Address Transform Map",
            group=self.transform_map_group,
            source_endpoint=ipaddress_endpoint,
            target_model=ipaddress_ct,
        )

        # Set Site as parent of both VRF and Interface
        tm_vrf.parents.add(tm_site)
        tm_interface.parents.add(tm_site)

        # Set both VRF and Interface as parents of IP Address (valid - no cycle)
        form = IPFabricTransformMapForm(
            instance=tm_ipaddress,
            data={
                "name": tm_ipaddress.name,
                "group": self.transform_map_group.pk,
                "source_endpoint": ipaddress_endpoint.pk,
                "target_model": ipaddress_ct.pk,
                "parents": [tm_vrf.pk, tm_interface.pk],
            },
        )

        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(tm_ipaddress.parents.count(), 2)
        self.assertIn(tm_vrf, tm_ipaddress.parents.all())
        self.assertIn(tm_interface, tm_ipaddress.parents.all())

    def test_self_as_parent_prevented_by_form_init(self):
        """Test that a transform map cannot be set as its own parent (prevented by form __init__)"""
        tm = IPFabricTransformMap.objects.create(
            name="Test Transform Map",
            group=self.transform_map_group,
            source_endpoint=self.device_endpoint,
            target_model=self.device_content_type,
        )

        # The form should exclude self from parents queryset
        form = IPFabricTransformMapForm(instance=tm)
        parents_queryset = form.fields["parents"].queryset
        self.assertNotIn(tm, parents_queryset)

    def test_no_validation_for_new_instances(self):
        """Test that circular dependency validation is skipped for new instances"""
        # New instance (no pk) should not trigger circular dependency validation
        form = IPFabricTransformMapForm(
            data={
                "name": "New Transform Map",
                "group": self.transform_map_group.pk,
                "source_endpoint": self.device_endpoint.pk,
                "target_model": self.device_content_type.pk,
                # parents field is optional and empty for new instances
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_no_validation_when_parents_empty(self):
        """Test that circular dependency validation is skipped when no parents are selected"""
        tm = IPFabricTransformMap.objects.create(
            name="Test Transform Map",
            group=self.transform_map_group,
            source_endpoint=self.device_endpoint,
            target_model=self.device_content_type,
        )

        # Edit without setting any parents
        form = IPFabricTransformMapForm(
            instance=tm,
            data={
                "name": "Updated Transform Map",
                "group": self.transform_map_group.pk,
                "source_endpoint": self.device_endpoint.pk,
                "target_model": self.device_content_type.pk,
                "parents": [],  # Empty parents
            },
        )

        self.assertTrue(form.is_valid(), form.errors)


class IPFabricTransformMapCloneFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.transform_map_group = IPFabricTransformMapGroup.objects.create(
            name="Test Group", description="Test group description"
        )

    def fields_are_required(self):
        form = IPFabricTransformMapCloneForm(data={})
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("name", form.errors)

    def test_fields_are_optional(self):
        form = IPFabricTransformMapCloneForm(
            data={
                "name": "Cloned Transform Map",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_clone_options_default_to_true(self):
        form = IPFabricTransformMapCloneForm(
            data={"name": "Cloned Transform Map", "group": self.transform_map_group.pk}
        )
        self.assertTrue(form.is_valid(), form.errors)
        # Check initial values
        self.assertTrue(form.fields["clone_fields"].initial)
        self.assertTrue(form.fields["clone_relationships"].initial)

    def test_valid_clone_form(self):
        form = IPFabricTransformMapCloneForm(
            data={
                "name": "Cloned Transform Map",
                "group": self.transform_map_group.pk,
                "clone_fields": False,
                "clone_relationships": True,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)


class IPFabricSnapshotFilterFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = IPFabricSource.objects.create(
            name="Test Source",
            type=IPFabricSourceTypeChoices.LOCAL,
            url="https://test.ipfabric.local",
            status=IPFabricSourceStatusChoices.NEW,
        )

    def test_all_fields_are_optional(self):
        form = IPFabricSnapshotFilterForm(data={})
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_filter_form_with_all_fields(self):
        form = IPFabricSnapshotFilterForm(
            data={
                "name": "Test Snapshot",
                "status": "loaded",
                "source_id": [self.source.pk],
                "snapshot_id": "test-snapshot-id",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)


class IPFabricSourceFilterFormTestCase(TestCase):
    def test_all_fields_are_optional(self):
        form = IPFabricSourceFilterForm(data={})
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_filter_form_with_status(self):
        form = IPFabricSourceFilterForm(
            data={
                "status": [
                    IPFabricSourceStatusChoices.NEW,
                    IPFabricSourceStatusChoices.COMPLETED,
                ]
            }
        )
        self.assertTrue(form.is_valid(), form.errors)


class IPFabricIngestionFilterFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.source = IPFabricSource.objects.create(
            name="Test Source",
            type=IPFabricSourceTypeChoices.LOCAL,
            url="https://test.ipfabric.local",
            status=IPFabricSourceStatusChoices.NEW,
        )

        cls.snapshot = IPFabricSnapshot.objects.create(
            name="Test Snapshot",
            source=cls.source,
            snapshot_id="test-snapshot-id",
            status=IPFabricSnapshotStatusModelChoices.STATUS_LOADED,
        )

        cls.sync = IPFabricSync.objects.create(
            name="Test Sync",
            snapshot_data=cls.snapshot,
        )

    def test_all_fields_are_optional(self):
        form = IPFabricIngestionFilterForm(data={})
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_filter_form_with_sync(self):
        form = IPFabricIngestionFilterForm(data={"sync_id": [self.sync.pk]})
        self.assertTrue(form.is_valid(), form.errors)


class IPFabricIngestionMergeFormTestCase(TestCase):
    def test_remove_branch_defaults_to_true(self):
        form = IPFabricIngestionMergeForm(data={"confirm": True})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.fields["remove_branch"].initial)

    def test_remove_branch_is_optional(self):
        form = IPFabricIngestionMergeForm(data={"confirm": True})
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_merge_form(self):
        form = IPFabricIngestionMergeForm(data={"confirm": True, "remove_branch": True})
        self.assertTrue(form.is_valid(), form.errors)


class IPFabricSyncFormTestCase(TestCase):
    maxDiff = 1500

    @classmethod
    def setUpTestData(cls):
        cls.source = IPFabricSource.objects.create(
            name="Test Source",
            type=IPFabricSourceTypeChoices.LOCAL,
            url="https://test.ipfabric.local",
            status=IPFabricSourceStatusChoices.NEW,
        )

        cls.snapshot = IPFabricSnapshot.objects.create(
            name="Test Snapshot",
            source=cls.source,
            snapshot_id="test-snapshot-id",
            status=IPFabricSnapshotStatusModelChoices.STATUS_LOADED,
            data={"sites": ["site1", "site2", "site3"]},
        )

        cls.transform_map_group = IPFabricTransformMapGroup.objects.create(
            name="Test Group", description="Test group description"
        )

    def test_fields_are_required(self):
        form = IPFabricSyncForm(data={})
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("name", form.errors)
        self.assertIn("source", form.errors)
        self.assertIn("snapshot_data", form.errors)

    def test_fields_are_optional(self):
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_sync_form(self):
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
                "auto_merge": True,
                "update_custom_fields": True,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_initialization_with_sites_no_data(self):
        """Test sites handling without data"""
        form = IPFabricSyncForm(initial={"sites": ["site1", "site2"]})

        # Verify that sites choices and initial values are set
        # Convert to list for comparison since form returns list, not tuple
        expected_choices = [("site1", "site1"), ("site2", "site2")]
        self.assertEqual(form.fields["sites"].choices, expected_choices)
        self.assertEqual(form.fields["sites"].initial, tuple(expected_choices))

    def test_form_initialization_with_snapshot_data_in_form_data(self):
        """Test form with data containing snapshot_data"""
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
            }
        )

        # Verify that site choices are set based on snapshot's sites when data exists
        expected_choices = [("site1", "site1"), ("site2", "site2"), ("site3", "site3")]
        self.assertEqual(form.fields["sites"].choices, expected_choices)
        self.assertEqual(self.snapshot.sites, ["site1", "site2", "site3"])

    def test_form_initialization_with_different_snapshot_sites(self):
        """Verify different snapshot sites are properly handled"""
        # Create another snapshot with different sites
        snapshot2 = IPFabricSnapshot.objects.create(
            name="Test Snapshot 2",
            source=self.source,
            snapshot_id="test-snapshot-id-2",
            status=IPFabricSnapshotStatusModelChoices.STATUS_LOADED,
            data={"sites": ["siteA", "siteB"]},
        )

        # Test form with the second snapshot
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync 2",
                "source": self.source.pk,
                "snapshot_data": snapshot2.pk,
            }
        )

        # Verify that the correct snapshot's sites are used
        # Convert to list for comparison since form returns list, not tuple
        expected_choices = [("siteA", "siteA"), ("siteB", "siteB")]
        self.assertEqual(form.fields["sites"].choices, expected_choices)

    def test_form_initialization_with_snapshot_no_sites_data(self):
        """Verify handling when snapshot has no sites data"""
        # Create a snapshot with no sites data
        snapshot_no_sites = IPFabricSnapshot.objects.create(
            name="Test Snapshot No Sites",
            source=self.source,
            snapshot_id="test-snapshot-no-sites",
            status=IPFabricSnapshotStatusModelChoices.STATUS_LOADED,
            data={},  # No sites data
        )

        # Test form with snapshot that has no sites
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync No Sites",
                "source": self.source.pk,
                "snapshot_data": snapshot_no_sites.pk,
            }
        )

        # Verify that sites choices are empty when snapshot has no sites
        sites_choices = form.fields["sites"].choices
        self.assertTrue(len(sites_choices) == 0)
        self.assertEqual(snapshot_no_sites.sites, [])

    def test_form_initialization_with_existing_instance_no_data(self):
        """Test existing instance initialization when not self.data"""
        # Create an existing sync instance
        sync_instance = IPFabricSync.objects.create(
            name="Existing Sync",
            snapshot_data=self.snapshot,
            parameters={
                "sites": ["site1", "site2"],
                "groups": [self.transform_map_group.pk],
            },
        )

        # Test form initialization with existing instance but no data
        form = IPFabricSyncForm(instance=sync_instance)

        # Verify that initial values are set from instance parameters
        self.assertEqual(form.initial["source"], self.source)
        self.assertEqual(form.initial["sites"], ["site1", "site2"])
        self.assertEqual(form.initial["groups"], [self.transform_map_group.pk])

        # Verify that sites choices are set from instance's snapshot when no data
        # Convert to list for comparison since form returns list, not tuple
        expected_choices = [("site1", "site1"), ("site2", "site2"), ("site3", "site3")]
        self.assertEqual(form.fields["sites"].choices, expected_choices)

    def test_form_initialization_with_existing_instance_and_initial_kwargs(self):
        """Test existing instance initialization with initial kwargs"""
        # Create an existing sync instance
        sync_instance = IPFabricSync.objects.create(
            name="Existing Sync",
            snapshot_data=self.snapshot,
            parameters={"sites": ["site1"], "groups": []},
        )

        # Test form initialization with existing instance and initial kwargs
        form = IPFabricSyncForm(
            instance=sync_instance, initial={"name": "Override Name"}
        )

        # These should be set from instance even when not in initial kwarg
        self.assertIn("source", form.initial)
        self.assertIn("sites", form.initial)
        self.assertIn("groups", form.initial)

        # But the provided initial value should be present
        self.assertEqual(form.initial.get("name"), "Override Name")

    def test_htmx_boolean_field_list_values_handled(self):
        """Test sanitizing HTMX BooleanField list values like ['', 'on']"""
        # Simulate HTMX request where BooleanField values become lists
        # This happens when `source` field value is changed and form is re-drawn via HTMX
        form = IPFabricSyncForm(
            initial={
                "auto_merge": ["", "on"],  # HTMX sends BooleanField as list
                "update_custom_fields": ["", "on"],  # Another BooleanField as list
                "name": "Test Sync",  # Normal field (not affected)
            },
            data={
                "name": "Test Sync HTMX",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
            },
        )

        # The last value from ['', 'on'] should be 'on' which evaluates to True for BooleanFields
        self.assertEqual(form.initial["auto_merge"], "on")
        self.assertEqual(form.initial["update_custom_fields"], "on")
        self.assertEqual(form.initial["name"], "Test Sync")  # Normal field unchanged

        # Verify the form is still valid and processes correctly
        self.assertTrue(form.is_valid(), form.errors)

    def test_sites_initial_value_set_from_form_initial(self):
        """Test that sites field initial is set from self.initial["sites"]"""
        # Create an existing sync instance with sites in parameters
        sync_instance = IPFabricSync.objects.create(
            name="Existing Sync",
            snapshot_data=self.snapshot,
            parameters={
                "sites": ["site1", "site2"],
                "groups": [self.transform_map_group.pk],
            },
        )

        # Initialize form with existing instance and additional initial data for sites
        # This will trigger the else branch where self.initial["sites"] is used
        form = IPFabricSyncForm(
            instance=sync_instance,
            initial={"sites": ["override_site1", "override_site2"]},
        )

        # Verify sites field initial is set from self.initial
        self.assertEqual(
            form.fields["sites"].initial, ["override_site1", "override_site2"]
        )

        # Also verify that self.initial contains the expected sites
        self.assertEqual(form.initial["sites"], ["override_site1", "override_site2"])

    def test_htmx_boolean_field_single_values_unchanged(self):
        """Test that normal single values are not affected by the HTMX list handling"""
        # Test with normal single values (not lists)
        form = IPFabricSyncForm(
            initial={
                "auto_merge": True,  # Normal boolean value
                "update_custom_fields": False,  # Normal boolean value
                "name": "Test Sync",  # Normal string value
            },
            data={
                "name": "Test Sync Normal",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
            },
        )

        # Verify that single values are not processed by value sanitization
        self.assertEqual(form.initial["auto_merge"], True)
        self.assertEqual(form.initial["update_custom_fields"], False)
        self.assertEqual(form.initial["name"], "Test Sync")

        # Verify the form is still valid
        self.assertTrue(form.is_valid(), form.errors)

    def test_clean_snapshot_does_not_belong_to_source(self):
        """Test form validation when snapshot doesn't belong to the selected source"""
        # Create a second source
        different_source = IPFabricSource.objects.create(
            name="Different Source",
            type=IPFabricSourceTypeChoices.LOCAL,
            url="https://different.ipfabric.local",
            status=IPFabricSourceStatusChoices.NEW,
        )

        # Try to use self.snapshot (which belongs to self.source) with different_source
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync Mismatched Source",
                "source": different_source.pk,
                "snapshot_data": self.snapshot.pk,  # This snapshot belongs to self.source, not different_source
            }
        )

        # Form should be invalid due to snapshot/source mismatch validation
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("snapshot_data", form.errors)
        self.assertTrue(
            "Snapshot does not belong to the selected source"
            in str(form.errors["snapshot_data"])
        )

    def test_clean_sites_not_part_of_snapshot(self):
        """Test form validation when selected sites are not part of the snapshot"""
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync Invalid Sites",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
                "sites": ["invalid_site1", "invalid_site2"],  # Sites not in snapshot
            }
        )

        # Form should be invalid due to sites validation
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("sites", form.errors)
        self.assertTrue("not part of the snapshot" in str(form.errors["sites"]))

    def test_clean_sites_validation_with_valid_sites(self):
        """Test form validation when selected sites are valid (part of the snapshot)"""
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync Valid Sites",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
                "sites": ["site1", "site2"],  # Valid sites that are in snapshot
            }
        )

        # Form should be valid since sites are part of the snapshot
        self.assertTrue(form.is_valid(), form.errors)

    def test_clean_sites_validation_with_partial_match(self):
        """Test form validation when some sites are valid and some are not"""
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync Partial Sites",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
                "sites": ["site1", "invalid_site"],  # Mix of valid and invalid sites
            }
        )

        # Form should be invalid since not all sites are part of the snapshot
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("sites", form.errors)
        self.assertTrue("not part of the snapshot" in str(form.errors["sites"]))

    def test_clean_sites_validation_without_sites(self):
        """Test form validation when no sites are selected (sites is None/empty)"""
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync No Sites",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
                # No sites specified
            }
        )

        # Form should be valid since the condition only triggers when sites exist
        self.assertTrue(form.is_valid(), form.errors)

    def test_clean_scheduled_time_in_past(self):
        """Test form validation when scheduled time is in the past"""
        past_time = local_now() - timedelta(hours=1)
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync Past Schedule",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
                "scheduled": past_time,
            }
        )

        # Form should be invalid due to scheduled time validation
        self.assertFalse(form.is_valid(), form.errors)
        self.assertTrue("Scheduled time must be in the future" in str(form.errors))

    def test_clean_interval_without_scheduled_time(self):
        """Test interval is provided without scheduled time"""
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync No Schedule",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
                "interval": 60,
                # No scheduled time specified
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNotNone(form.cleaned_data["scheduled"])

    def test_clean_groups_missing_required_transform_maps(self):
        """Test form validation when transform map groups are missing required maps"""
        # Delete a required default transform map to trigger validation failure
        # This ensures that the missing map cannot be covered by default maps
        manufacturer_content_type = ContentType.objects.get(
            app_label="dcim", model="manufacturer"
        )
        IPFabricTransformMap.objects.filter(
            target_model=manufacturer_content_type, group__isnull=True
        ).delete()

        form = IPFabricSyncForm(
            data={
                "name": "Test Sync Missing Maps",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
            }
        )

        # Form should be invalid due to missing required transform maps
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("groups", form.errors)
        self.assertTrue("Missing maps:" in str(form.errors["groups"]))
        # Check that it mentions some of the missing required maps
        error_message = str(form.errors["groups"])
        self.assertTrue("dcim.manufacturer" in error_message, error_message)

    def test_save_method_basic_functionality(self):
        """Test basic save functionality without scheduling"""
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync Save",
                "sites": ["site1", "site2"],
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
                "groups": [self.transform_map_group.pk],
                "auto_merge": True,
                "update_custom_fields": True,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

        # Save the form
        sync_instance = form.save()

        # Verify the instance was created correctly
        self.assertIsInstance(sync_instance, IPFabricSync)
        self.assertEqual(sync_instance.name, "Test Sync Save")
        self.assertEqual(sync_instance.snapshot_data.source, self.source)
        self.assertEqual(sync_instance.snapshot_data, self.snapshot)
        self.assertEqual(sync_instance.status, IPFabricSyncStatusChoices.NEW)
        self.assertTrue(sync_instance.auto_merge)
        self.assertTrue(sync_instance.update_custom_fields)

        # Verify parameters were stored correctly
        # All models are `False` since checkboxes must always default to False
        expected_parameters = {
            "sites": ["site1", "site2"],
            "groups": [self.transform_map_group.pk],
            "dcim.site": False,
            "dcim.manufacturer": False,
            "dcim.devicetype": False,
            "dcim.devicerole": False,
            "dcim.platform": False,
            "dcim.device": False,
            "dcim.virtualchassis": False,
            "dcim.interface": False,
            "dcim.macaddress": False,
            "dcim.inventoryitem": False,
            "ipam.vlan": False,
            "ipam.vrf": False,
            "ipam.prefix": False,
            "ipam.ipaddress": False,
        }
        self.assertEqual(sync_instance.parameters, expected_parameters)

    def test_save_method_with_model_parameters(self):
        """Test save method properly handles model parameters form fields"""
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync IPF Params",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
                "dcim.site": True,
                "dcim.interface": True,
                "ipam.prefix": True,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

        sync_instance = form.save()

        # Verify parameters were stripped and stored correctly
        # All models are `False` since checkboxes must always default to False
        expected_parameters = {
            "sites": [],
            "groups": [],
            "dcim.site": True,  # Explicitly set
            "dcim.manufacturer": False,
            "dcim.devicetype": False,
            "dcim.devicerole": False,
            "dcim.platform": False,
            "dcim.device": False,
            "dcim.virtualchassis": False,
            "dcim.interface": True,  # Explicitly set
            "dcim.macaddress": False,
            "dcim.inventoryitem": False,
            "ipam.ipaddress": False,
            "ipam.vlan": False,
            "ipam.vrf": False,
            "ipam.prefix": True,  # Explicitly set
        }
        self.assertEqual(sync_instance.parameters, expected_parameters)

    @patch("ipfabric_netbox.models.IPFabricSync.enqueue_sync_job")
    def test_save_method_with_scheduling_no_interval(self, mock_enqueue):
        """Test save method with scheduled time but no interval"""
        future_time = local_now() + timedelta(hours=1)

        form = IPFabricSyncForm(
            data={
                "name": "Test Sync Scheduled",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
                "scheduled": future_time,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

        # Capture the time before save to compare - with more tolerance
        sync_instance = form.save()

        # Verify the instance was created correctly
        self.assertEqual(sync_instance.scheduled, future_time)
        self.assertIsNone(sync_instance.interval)

        # Verify the instance exists in database
        saved_instance = IPFabricSync.objects.get(pk=sync_instance.pk)
        self.assertEqual(saved_instance.scheduled, future_time)

        # Verify that enqueue_sync_job was called when object.scheduled is set
        mock_enqueue.assert_called_once()

    @patch("ipfabric_netbox.models.IPFabricSync.enqueue_sync_job")
    def test_save_method_with_interval_auto_schedule(self, mock_enqueue):
        """Test save method with interval automatically schedules for current time"""
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync Interval",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
                "interval": 60,
                # No scheduled time specified
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

        # Capture the time before save to compare - with more tolerance
        before_save = local_now() - timedelta(seconds=1)
        sync_instance = form.save()
        after_save = local_now() + timedelta(seconds=1)

        # Verify interval was set and scheduled time was auto-generated
        self.assertEqual(sync_instance.interval, 60)
        self.assertIsNotNone(sync_instance.scheduled)

        # Scheduled time should be close to current time (within the test execution window)
        self.assertTrue(before_save <= sync_instance.scheduled <= after_save)

        # Verify that enqueue_sync_job was called when object.scheduled is set
        mock_enqueue.assert_called_once()

    @patch("ipfabric_netbox.models.IPFabricSync.enqueue_sync_job")
    def test_save_method_with_both_scheduled_and_interval(self, mock_enqueue):
        """Test save method with both scheduled time and interval"""
        future_time = local_now() + timedelta(hours=2)

        form = IPFabricSyncForm(
            data={
                "name": "Test Sync Both",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
                "scheduled": future_time,
                "interval": 120,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

        sync_instance = form.save()

        # Verify both values were set correctly
        self.assertEqual(sync_instance.scheduled, future_time)
        self.assertEqual(sync_instance.interval, 120)

        # Verify that enqueue_sync_job was called when object.scheduled is set
        mock_enqueue.assert_called_once()

    def test_save_method_empty_sites_and_groups(self):
        """Test save method handles empty sites and groups correctly"""
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync Empty",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
                # No sites or groups specified
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

        sync_instance = form.save()

        # Verify empty collections are handled correctly
        self.assertEqual(sync_instance.parameters["sites"], [])
        self.assertEqual(sync_instance.parameters["groups"], [])

    def test_save_method_status_always_set_to_new(self):
        """Test that save method always sets status to NEW regardless of input"""
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync Status",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

        sync_instance = form.save()

        # Status should always be NEW after save
        self.assertEqual(sync_instance.status, IPFabricSyncStatusChoices.NEW)

        # Verify in database as well
        saved_instance = IPFabricSync.objects.get(pk=sync_instance.pk)
        self.assertEqual(saved_instance.status, IPFabricSyncStatusChoices.NEW)

    def test_fieldsets_for_local_source_type(self):
        """Test that fieldsets returns correct structure for local source type"""
        form = IPFabricSyncForm(
            data={
                "name": "Test Sync",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
            }
        )

        fieldsets = form.fieldsets

        # Should have multiple fieldsets
        self.assertGreater(len(fieldsets), 5)

        # First fieldset should be IP Fabric Source
        self.assertEqual(fieldsets[0].name, "IP Fabric Source")

        # Second fieldset should be Snapshot Information with sites for local source
        self.assertEqual(fieldsets[1].name, "Snapshot Information")

        # Should contain Ingestion Execution Parameters fieldset
        exec_params_fieldset = next(
            (fs for fs in fieldsets if fs.name == "Ingestion Execution Parameters"),
            None,
        )
        self.assertIsNotNone(exec_params_fieldset)

        # Should contain Extras fieldset
        extras_fieldset = next((fs for fs in fieldsets if fs.name == "Extras"), None)
        self.assertIsNotNone(extras_fieldset)

        # Should contain Tags fieldset
        tags_fieldset = next((fs for fs in fieldsets if fs.name == "Tags"), None)
        self.assertIsNotNone(tags_fieldset)

    def test_fieldsets_for_remote_source_type(self):
        """Test that fieldsets returns correct structure for remote source type"""
        # Create a remote source
        remote_source = IPFabricSource.objects.create(
            name="Test Remote Source",
            type=IPFabricSourceTypeChoices.REMOTE,
            url="https://remote.ipfabric.local",
            status=IPFabricSourceStatusChoices.NEW,
        )

        remote_snapshot = IPFabricSnapshot.objects.create(
            name="Test Remote Snapshot",
            source=remote_source,
            snapshot_id="test-remote-snapshot-id",
            status=IPFabricSnapshotStatusModelChoices.STATUS_LOADED,
            data={"sites": ["remote_site1", "remote_site2"]},
        )

        form = IPFabricSyncForm(
            data={
                "name": "Test Remote Sync",
                "source": remote_source.pk,
                "snapshot_data": remote_snapshot.pk,
            }
        )

        fieldsets = form.fieldsets

        # Should have multiple fieldsets
        self.assertGreater(len(fieldsets), 5)

        # First fieldset should be IP Fabric Source
        self.assertEqual(fieldsets[0].name, "IP Fabric Source")

        # Second fieldset should be Snapshot Information without sites for remote source
        self.assertEqual(fieldsets[1].name, "Snapshot Information")

        # Verify the fieldsets structure is consistent
        fieldset_names = [fs.name for fs in fieldsets]
        expected_names = [
            "IP Fabric Source",
            "Snapshot Information",
            "Extras",
            "Tags",
        ]

        for expected_name in expected_names:
            self.assertIn(expected_name, fieldset_names)

    def test_fieldsets_with_existing_instance_local_source(self):
        """Test fieldsets behavior with an existing sync instance from local source"""
        # Create an existing sync instance
        sync_instance = IPFabricSync.objects.create(
            name="Existing Sync",
            snapshot_data=self.snapshot,
            parameters={
                "sites": ["site1", "site2"],
                "groups": [self.transform_map_group.pk],
            },
        )

        form = IPFabricSyncForm(instance=sync_instance)
        fieldsets = form.fieldsets

        # Should have multiple fieldsets
        self.assertGreater(len(fieldsets), 5)

        # First fieldset should be IP Fabric Source
        self.assertEqual(fieldsets[0].name, "IP Fabric Source")

        # Second fieldset should be Snapshot Information with sites (local source)
        self.assertEqual(fieldsets[1].name, "Snapshot Information")

        # Should contain parameter fieldsets for ALL type
        fieldset_names = [fs.name for fs in fieldsets]
        self.assertIn("DCIM Parameters", fieldset_names)
        self.assertIn("IPAM Parameters", fieldset_names)

    def test_fieldsets_property_returns_correct_field_types(self):
        """Test that fieldsets property returns FieldSet objects with correct structure"""

        form = IPFabricSyncForm(
            data={
                "name": "Test Sync",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
            }
        )

        fieldsets = form.fieldsets

        # Each item should be a FieldSet instance
        for fieldset in fieldsets:
            self.assertIsInstance(fieldset, FieldSet)
            # Each fieldset should have a name
            self.assertIsNotNone(fieldset.name)

    def test_fieldsets_dynamic_behavior_consistency(self):
        """Test that fieldsets method consistently returns the same structure for same parameters"""
        # Test consistency for same parameters
        form1 = IPFabricSyncForm(
            data={
                "name": "Test Sync 1",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
            }
        )
        form2 = IPFabricSyncForm(
            data={
                "name": "Test Sync 2",
                "source": self.source.pk,
                "snapshot_data": self.snapshot.pk,
            }
        )

        fieldsets1 = form1.fieldsets
        fieldsets2 = form2.fieldsets

        # Both should have the same structure
        self.assertEqual(len(fieldsets1), len(fieldsets2))

        fieldset_names1 = [fs.name for fs in fieldsets1]
        fieldset_names2 = [fs.name for fs in fieldsets2]
        self.assertEqual(fieldset_names1, fieldset_names2)


class IPFabricFilterFormTestCase(TestCase):
    """Test cases for IPFabricFilterForm"""

    @classmethod
    def setUpTestData(cls):
        # Create endpoints for testing
        cls.endpoint1 = IPFabricEndpoint.objects.get(endpoint="/inventory/devices")
        cls.endpoint2 = IPFabricEndpoint.objects.get(endpoint="/inventory/interfaces")

        # Create filter expressions for testing
        cls.expression1 = IPFabricFilterExpression.objects.create(
            name="Test Expression 1",
            description="First test expression",
            expression=[{"siteName": ["eq", "Site1"]}],
        )
        cls.expression2 = IPFabricFilterExpression.objects.create(
            name="Test Expression 2",
            description="Second test expression",
            expression=[{"hostname": ["like", "router"]}],
        )

        # Create a sync object for testing
        cls.source = IPFabricSource.objects.create(
            name="Test Source",
            type=IPFabricSourceTypeChoices.LOCAL,
            url="https://test.ipfabric.local",
            status=IPFabricSourceStatusChoices.NEW,
        )
        cls.snapshot = IPFabricSnapshot.objects.create(
            name="Test Snapshot",
            source=cls.source,
            snapshot_id="test-snapshot-id",
            status=IPFabricSnapshotStatusModelChoices.STATUS_LOADED,
            data={"sites": ["site1", "site2"]},
        )
        cls.sync = IPFabricSync.objects.create(
            name="Test Sync",
            snapshot_data=cls.snapshot,
        )

    def test_fields_are_required(self):
        """Test that required fields are validated"""
        form = IPFabricFilterForm(data={})
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("name", form.errors)
        self.assertIn("filter_type", form.errors)

    def test_fields_are_optional(self):
        """Test that optional fields work correctly"""
        form = IPFabricFilterForm(
            data={
                "name": "Test Filter",
                "filter_type": IPFabricFilterTypeChoices.AND,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_filter_form_with_all_fields(self):
        """Test valid form submission with all fields"""
        form = IPFabricFilterForm(
            data={
                "name": "Test Filter Complete",
                "description": "A complete test filter",
                "filter_type": IPFabricFilterTypeChoices.OR,
                "endpoints": [self.endpoint1.pk, self.endpoint2.pk],
                "syncs": [self.sync.pk],
                "expressions": [self.expression1.pk, self.expression2.pk],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()

        # Verify the instance was created correctly
        self.assertEqual(instance.name, "Test Filter Complete")
        self.assertEqual(instance.description, "A complete test filter")
        self.assertEqual(instance.filter_type, IPFabricFilterTypeChoices.OR)

        # Verify many-to-many relationships
        self.assertEqual(
            list(instance.endpoints.all()), [self.endpoint1, self.endpoint2]
        )
        self.assertEqual(list(instance.syncs.all()), [self.sync])
        self.assertEqual(
            list(instance.expressions.all().order_by("pk")),
            [self.expression1, self.expression2],
        )

    def test_valid_filter_form_with_and_type(self):
        """Test form with AND filter type"""
        form = IPFabricFilterForm(
            data={
                "name": "AND Filter",
                "filter_type": IPFabricFilterTypeChoices.AND,
                "expressions": [self.expression1.pk],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.filter_type, IPFabricFilterTypeChoices.AND)

    def test_valid_filter_form_with_or_type(self):
        """Test form with OR filter type"""
        form = IPFabricFilterForm(
            data={
                "name": "OR Filter",
                "filter_type": IPFabricFilterTypeChoices.OR,
                "expressions": [self.expression2.pk],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.filter_type, IPFabricFilterTypeChoices.OR)

    def test_filter_type_must_be_valid_choice(self):
        """Test that filter_type must be a valid choice"""
        form = IPFabricFilterForm(
            data={
                "name": "Invalid Filter",
                "filter_type": "invalid_type",
            }
        )
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("filter_type", form.errors)

    def test_form_initialization_with_existing_instance(self):
        """Test that when editing an existing filter, expressions are properly initialized"""
        # Create an existing filter with expressions
        existing_filter = IPFabricFilter.objects.create(
            name="Existing Filter",
            filter_type=IPFabricFilterTypeChoices.AND,
        )
        existing_filter.expressions.set([self.expression1, self.expression2])

        # Initialize form with the existing instance
        form = IPFabricFilterForm(instance=existing_filter)

        # Verify that expressions initial is set correctly
        expected_ids = list(
            existing_filter.expressions.all().values_list("id", flat=True)
        )
        actual_initial = (
            list(form.fields["expressions"].initial)
            if form.fields["expressions"].initial
            else []
        )
        self.assertEqual(actual_initial, expected_ids)

    def test_form_initialization_with_new_instance(self):
        """Test form initialization for a new instance (no pk)"""
        # Create a new instance without saving
        new_filter = IPFabricFilter(
            name="New Filter",
            filter_type=IPFabricFilterTypeChoices.OR,
        )

        # Initialize form with new instance (no pk)
        form = IPFabricFilterForm(instance=new_filter)

        # Initial should not be set since instance.pk is None
        self.assertIsNone(form.fields["expressions"].initial)

    def test_save_method_sets_expressions(self):
        """Test that save method properly sets the expressions relationship"""
        form = IPFabricFilterForm(
            data={
                "name": "Filter with Expressions",
                "filter_type": IPFabricFilterTypeChoices.AND,
                "expressions": [self.expression1.pk, self.expression2.pk],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

        instance = form.save()

        # Verify expressions were set correctly
        expression_ids = list(instance.expressions.all().values_list("id", flat=True))
        self.assertIn(self.expression1.pk, expression_ids)
        self.assertIn(self.expression2.pk, expression_ids)
        self.assertEqual(len(expression_ids), 2)

    def test_save_method_updates_expressions(self):
        """Test that save method properly updates expressions on existing instance"""
        # Create an existing filter with one expression
        existing_filter = IPFabricFilter.objects.create(
            name="Existing Filter",
            filter_type=IPFabricFilterTypeChoices.AND,
        )
        existing_filter.expressions.set([self.expression1])

        # Update the filter to use different expressions
        form = IPFabricFilterForm(
            data={
                "name": "Updated Filter",
                "filter_type": IPFabricFilterTypeChoices.OR,
                "expressions": [self.expression2.pk],
            },
            instance=existing_filter,
        )
        self.assertTrue(form.is_valid(), form.errors)

        updated_instance = form.save()

        # Verify expressions were updated
        expression_ids = list(
            updated_instance.expressions.all().values_list("id", flat=True)
        )
        self.assertEqual(expression_ids, [self.expression2.pk])
        self.assertEqual(updated_instance.filter_type, IPFabricFilterTypeChoices.OR)

    def test_save_method_clears_expressions(self):
        """Test that save method can clear all expressions"""
        # Create an existing filter with expressions
        existing_filter = IPFabricFilter.objects.create(
            name="Filter with Expressions",
            filter_type=IPFabricFilterTypeChoices.AND,
        )
        existing_filter.expressions.set([self.expression1, self.expression2])

        # Update the filter to have no expressions
        form = IPFabricFilterForm(
            data={
                "name": "Filter without Expressions",
                "filter_type": IPFabricFilterTypeChoices.AND,
                "expressions": [],
            },
            instance=existing_filter,
        )
        self.assertTrue(form.is_valid(), form.errors)

        updated_instance = form.save()

        # Verify expressions were cleared
        self.assertEqual(updated_instance.expressions.count(), 0)

    def test_form_with_multiple_endpoints(self):
        """Test form with multiple endpoints"""
        form = IPFabricFilterForm(
            data={
                "name": "Multi-Endpoint Filter",
                "filter_type": IPFabricFilterTypeChoices.AND,
                "endpoints": [self.endpoint1.pk, self.endpoint2.pk],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()

        self.assertEqual(instance.endpoints.count(), 2)
        self.assertIn(self.endpoint1, instance.endpoints.all())
        self.assertIn(self.endpoint2, instance.endpoints.all())

    def test_form_with_multiple_syncs(self):
        """Test form with multiple syncs"""
        # Create another sync
        sync2 = IPFabricSync.objects.create(
            name="Test Sync 2",
            snapshot_data=self.snapshot,
        )

        form = IPFabricFilterForm(
            data={
                "name": "Multi-Sync Filter",
                "filter_type": IPFabricFilterTypeChoices.OR,
                "syncs": [self.sync.pk, sync2.pk],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()

        self.assertEqual(instance.syncs.count(), 2)
        self.assertIn(self.sync, instance.syncs.all())
        self.assertIn(sync2, instance.syncs.all())

    def test_form_without_optional_fields(self):
        """Test that form works without any optional fields"""
        form = IPFabricFilterForm(
            data={
                "name": "Minimal Filter",
                "filter_type": IPFabricFilterTypeChoices.AND,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()

        self.assertEqual(instance.name, "Minimal Filter")
        self.assertEqual(instance.endpoints.count(), 0)
        self.assertEqual(instance.syncs.count(), 0)
        self.assertEqual(instance.expressions.count(), 0)


class IPFabricFilterExpressionFormTestCase(TestCase):
    """Test cases for IPFabricFilterExpressionForm"""

    @classmethod
    def setUpTestData(cls):
        # Create filters for testing
        cls.filter1 = IPFabricFilter.objects.create(
            name="Test Filter 1",
            filter_type=IPFabricFilterTypeChoices.AND,
        )
        cls.filter2 = IPFabricFilter.objects.create(
            name="Test Filter 2",
            filter_type=IPFabricFilterTypeChoices.OR,
        )

    def test_fields_are_required(self):
        """Test that required fields are validated"""
        form = IPFabricFilterExpressionForm(data={})
        self.assertFalse(form.is_valid(), form.errors)
        self.assertIn("name", form.errors)
        self.assertIn("expression", form.errors)

    def test_fields_are_optional(self):
        """Test that optional fields work correctly"""
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Test Expression",
                "expression": [{"siteName": ["eq", "Site1"]}],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_expression_form_with_all_fields(self):
        """Test valid form submission with all fields"""
        expression_data = [{"siteName": ["eq", "Site1"]}]
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Complete Expression",
                "description": "A complete test expression",
                "expression": expression_data,
                "filters": [self.filter1.pk, self.filter2.pk],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()

        # Verify the instance was created correctly
        self.assertEqual(instance.name, "Complete Expression")
        self.assertEqual(instance.description, "A complete test expression")
        self.assertEqual(instance.expression, expression_data)

        # Verify many-to-many relationships
        self.assertEqual(instance.filters.count(), 2)
        self.assertIn(self.filter1, instance.filters.all())
        self.assertIn(self.filter2, instance.filters.all())

    def test_valid_expression_with_simple_filter(self):
        """Test form with a simple site name filter"""
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Site Filter",
                "expression": [{"siteName": ["eq", "Site1"]}],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.expression, [{"siteName": ["eq", "Site1"]}])

    def test_valid_expression_with_hostname_filter(self):
        """Test form with hostname like filter"""
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Hostname Filter",
                "expression": [{"hostname": ["like", "router"]}],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.expression, [{"hostname": ["like", "router"]}])

    def test_valid_expression_with_complex_filter(self):
        """Test form with complex nested filter expression"""
        complex_expression = [
            {
                "or": [
                    {"siteName": ["eq", "Site1"]},
                    {"siteName": ["eq", "Site2"]},
                ]
            }
        ]
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Complex Expression",
                "expression": complex_expression,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.expression, complex_expression)

    def test_valid_expression_with_multiple_conditions(self):
        """Test form with multiple filter conditions"""
        multi_condition_expression = [
            {"siteName": ["eq", "Site1"]},
            {"hostname": ["like", "switch"]},
        ]
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Multi Condition",
                "expression": multi_condition_expression,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.expression, multi_condition_expression)

    def test_expression_must_be_valid_json(self):
        """Test that expression field accepts valid JSON"""

        # Valid JSON that will be parsed
        valid_json_str = json.dumps([{"siteName": ["eq", "Site1"]}])
        form = IPFabricFilterExpressionForm(
            data={
                "name": "JSON Expression",
                "expression": json.loads(valid_json_str),  # Pass as Python object
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_with_single_filter(self):
        """Test form with a single filter"""
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Single Filter Expression",
                "expression": [{"siteName": ["eq", "Site1"]}],
                "filters": [self.filter1.pk],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()

        self.assertEqual(instance.filters.count(), 1)
        self.assertIn(self.filter1, instance.filters.all())

    def test_form_with_multiple_filters(self):
        """Test form with multiple filters"""
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Multi Filter Expression",
                "expression": [{"hostname": ["like", "core"]}],
                "filters": [self.filter1.pk, self.filter2.pk],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()

        self.assertEqual(instance.filters.count(), 2)
        self.assertIn(self.filter1, instance.filters.all())
        self.assertIn(self.filter2, instance.filters.all())

    def test_form_without_filters(self):
        """Test that form works without any filters"""
        form = IPFabricFilterExpressionForm(
            data={
                "name": "No Filter Expression",
                "expression": [{"siteName": ["eq", "Site1"]}],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()

        self.assertEqual(instance.filters.count(), 0)

    def test_form_without_description(self):
        """Test that description is optional"""
        form = IPFabricFilterExpressionForm(
            data={
                "name": "No Description",
                "expression": [{"siteName": ["eq", "Site1"]}],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.description, "")

    def test_form_with_description(self):
        """Test form with description field"""
        description = "This is a detailed description of the filter expression"
        form = IPFabricFilterExpressionForm(
            data={
                "name": "With Description",
                "description": description,
                "expression": [{"siteName": ["eq", "Site1"]}],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.description, description)

    def test_form_update_existing_expression(self):
        """Test updating an existing expression"""
        # Create an existing expression
        existing_expression = IPFabricFilterExpression.objects.create(
            name="Existing Expression",
            expression=[{"siteName": ["eq", "OldSite"]}],
        )
        existing_expression.filters.set([self.filter1])

        # Update it
        new_expression_data = [{"siteName": ["eq", "NewSite"]}]
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Updated Expression",
                "description": "Updated description",
                "expression": new_expression_data,
                "filters": [self.filter2.pk],
            },
            instance=existing_expression,
        )
        self.assertTrue(form.is_valid(), form.errors)
        updated_instance = form.save()

        # Verify updates
        self.assertEqual(updated_instance.name, "Updated Expression")
        self.assertEqual(updated_instance.description, "Updated description")
        self.assertEqual(updated_instance.expression, new_expression_data)
        self.assertEqual(list(updated_instance.filters.all()), [self.filter2])

    def test_form_clear_filters(self):
        """Test clearing all filters from an existing expression"""
        # Create an existing expression with filters
        existing_expression = IPFabricFilterExpression.objects.create(
            name="Expression with Filters",
            expression=[{"siteName": ["eq", "Site1"]}],
        )
        existing_expression.filters.set([self.filter1, self.filter2])

        # Clear filters
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Expression without Filters",
                "expression": [{"siteName": ["eq", "Site1"]}],
                "filters": [],
            },
            instance=existing_expression,
        )
        self.assertTrue(form.is_valid(), form.errors)
        updated_instance = form.save()

        # Verify filters were cleared
        self.assertEqual(updated_instance.filters.count(), 0)

    def test_name_must_be_unique(self):
        """Test that name field must be unique"""
        # Create first expression
        IPFabricFilterExpression.objects.create(
            name="Unique Name",
            expression=[{"siteName": ["eq", "Site1"]}],
        )

        # Try to create another with same name
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Unique Name",
                "expression": [{"siteName": ["eq", "Site2"]}],
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_textarea_widget_for_expression(self):
        """Test that expression field uses Textarea widget with monospace class"""
        form = IPFabricFilterExpressionForm()
        expression_widget = form.fields["expression"].widget

        # Check widget type
        self.assertIsInstance(expression_widget, forms.Textarea)

        # Check that it has the monospace class
        self.assertIn("class", expression_widget.attrs)
        self.assertIn("font-monospace", expression_widget.attrs["class"])

    def test_form_with_various_operator_types(self):
        """Test expressions with various operator types"""
        operators = [
            [{"siteName": ["eq", "Site1"]}],  # equals
            [{"hostname": ["like", "%router%"]}],  # like
            [{"hostname": ["reg", "^switch.*"]}],  # regex
            [{"vlan": ["gt", 100]}],  # greater than
            [{"vlan": ["lt", 200]}],  # less than
        ]

        for i, expression_data in enumerate(operators):
            form = IPFabricFilterExpressionForm(
                data={
                    "name": f"Operator Test {i}",
                    "expression": expression_data,
                }
            )
            self.assertTrue(
                form.is_valid(), f"Form invalid for {expression_data}: {form.errors}"
            )
            instance = form.save()
            self.assertEqual(instance.expression, expression_data)

    def test_form_minimal_required_fields(self):
        """Test form with only minimal required fields"""
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Minimal Expression",
                "expression": [{"siteName": ["eq", "Site1"]}],
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()

        self.assertEqual(instance.name, "Minimal Expression")
        self.assertEqual(instance.expression, [{"siteName": ["eq", "Site1"]}])
        self.assertEqual(instance.description, "")
        self.assertEqual(instance.filters.count(), 0)

    def test_expression_must_be_list(self):
        """Test that expression must be a list (validation at model level)"""
        # Try to save with a string instead of list
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Invalid String Expression",
                "expression": "not a list",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("expression", form.errors)

    def test_expression_cannot_be_empty_list(self):
        """Test that expression cannot be an empty list (validation at model level)"""
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Empty List Expression",
                "expression": [],
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("expression", form.errors)

    def test_expression_must_contain_dictionaries(self):
        """Test that expression items must be dictionaries (validation at model level)"""
        # Test with list containing strings
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Invalid List Items",
                "expression": ["string1", "string2"],
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("expression", form.errors)

    def test_expression_with_mixed_types(self):
        """Test that expression rejects mixed types in list (validation at model level)"""
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Mixed Types Expression",
                "expression": [{"siteName": ["eq", "Site1"]}, "not a dict", 123],
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("expression", form.errors)

    def test_expression_with_list_of_integers(self):
        """Test that expression rejects list of integers (validation at model level)"""
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Integer List Expression",
                "expression": [1, 2, 3],
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("expression", form.errors)

    def test_expression_with_nested_structure(self):
        """Test that expression accepts complex nested dictionary structures"""
        complex_expr = [
            {
                "and": [
                    {"siteName": ["eq", "Site1"]},
                    {
                        "or": [
                            {"hostname": ["like", "router%"]},
                            {"hostname": ["like", "switch%"]},
                        ]
                    },
                ]
            }
        ]
        form = IPFabricFilterExpressionForm(
            data={
                "name": "Nested Structure Expression",
                "expression": complex_expr,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.expression, complex_expr)

    def test_form_init_sets_test_source_initial_when_single_source(self):
        """Test that form __init__ sets test_source initial value when only one LOCAL source exists"""

        # Create a LOCAL source
        source = IPFabricSource.objects.create(
            name="Test Local Source",
            type=IPFabricSourceTypeChoices.LOCAL,
            url="https://test.local",
        )

        # Create snapshot and sync with LOCAL source
        snapshot = IPFabricSnapshot.objects.create(
            name="Test Snapshot",
            source=source,
        )
        sync = IPFabricSync.objects.create(
            name="Test Sync",
            snapshot_data=snapshot,
        )

        # Create filter with endpoint
        filter_obj = IPFabricFilter.objects.create(
            name="Test Filter with Source",
            filter_type=IPFabricFilterTypeChoices.AND,
        )
        filter_obj.syncs.add(sync)

        # Create expression and associate with filter
        expression = IPFabricFilterExpression.objects.create(
            name="Expression with Single Source",
            expression=[{"siteName": ["eq", "Site1"]}],
        )
        expression.filters.add(filter_obj)

        # Create form with instance - should set test_source initial value
        form = IPFabricFilterExpressionForm(instance=expression)

        # Verify test_source initial value is set
        self.assertEqual(form.fields["test_source"].initial, source)

    def test_form_init_sets_test_endpoint_initial_when_single_endpoint(self):
        """Test that form __init__ sets test_endpoint initial value when only one endpoint exists"""

        # Get or create an endpoint
        endpoint = IPFabricEndpoint.objects.first()
        if not endpoint:
            endpoint = IPFabricEndpoint.objects.create(
                name="Test Endpoint", endpoint="/tables/devices"
            )

        # Create filter with endpoint
        filter_obj = IPFabricFilter.objects.create(
            name="Test Filter with Endpoint",
            filter_type=IPFabricFilterTypeChoices.AND,
        )
        filter_obj.endpoints.add(endpoint)

        # Create expression and associate with filter
        expression = IPFabricFilterExpression.objects.create(
            name="Expression with Single Endpoint",
            expression=[{"siteName": ["eq", "Site1"]}],
        )
        expression.filters.add(filter_obj)

        # Create form with instance - should set test_endpoint initial value
        form = IPFabricFilterExpressionForm(instance=expression)

        # Verify test_endpoint initial value is set
        self.assertEqual(form.fields["test_endpoint"].initial, endpoint)

    def test_form_init_does_not_set_initial_when_multiple_sources(self):
        """Test that form __init__ does not set test_source when multiple LOCAL sources exist"""

        # Create two LOCAL sources
        source1 = IPFabricSource.objects.create(
            name="Test Local Source 1",
            type=IPFabricSourceTypeChoices.LOCAL,
            url="https://test1.local",
        )
        source2 = IPFabricSource.objects.create(
            name="Test Local Source 2",
            type=IPFabricSourceTypeChoices.LOCAL,
            url="https://test2.local",
        )

        # Create snapshots and syncs
        snapshot1 = IPFabricSnapshot.objects.create(
            name="Test Snapshot 1", source=source1
        )
        snapshot2 = IPFabricSnapshot.objects.create(
            name="Test Snapshot 2", source=source2
        )

        sync1 = IPFabricSync.objects.create(
            name="Test Sync 1",
            snapshot_data=snapshot1,
        )
        sync2 = IPFabricSync.objects.create(
            name="Test Sync 2",
            snapshot_data=snapshot2,
        )

        # Create two filters with different syncs
        filter1 = IPFabricFilter.objects.create(
            name="Test Filter for Source 1",
            filter_type=IPFabricFilterTypeChoices.AND,
        )
        filter1.syncs.add(sync1)

        filter2 = IPFabricFilter.objects.create(
            name="Test Filter for Source 2",
            filter_type=IPFabricFilterTypeChoices.AND,
        )
        filter2.syncs.add(sync2)

        # Create expression and associate with both filters
        expression = IPFabricFilterExpression.objects.create(
            name="Expression with Multiple Sources",
            expression=[{"siteName": ["eq", "Site1"]}],
        )
        expression.filters.add(filter1, filter2)

        # Create form with instance - should NOT set test_source initial value
        form = IPFabricFilterExpressionForm(instance=expression)

        # Verify test_source initial value is NOT set
        self.assertIsNone(form.fields["test_source"].initial)

    def test_form_init_does_not_set_initial_when_multiple_endpoints(self):
        """Test that form __init__ does not set test_endpoint when multiple endpoints exist"""

        # Get or create two endpoints
        endpoint1 = IPFabricEndpoint.objects.filter(endpoint="/tables/devices").first()
        endpoint2 = IPFabricEndpoint.objects.filter(endpoint="/tables/sites").first()

        if not endpoint1:
            endpoint1 = IPFabricEndpoint.objects.create(
                name="Devices Endpoint", endpoint="/tables/devices"
            )
        if not endpoint2:
            endpoint2 = IPFabricEndpoint.objects.create(
                name="Sites Endpoint", endpoint="/tables/sites"
            )

        # Create two filters with different endpoints
        filter1 = IPFabricFilter.objects.create(
            name="Test Filter Devices",
            filter_type=IPFabricFilterTypeChoices.AND,
        )
        filter1.endpoints.add(endpoint1)

        filter2 = IPFabricFilter.objects.create(
            name="Test Filter Sites",
            filter_type=IPFabricFilterTypeChoices.AND,
        )
        filter2.endpoints.add(endpoint2)

        # Create expression and associate with both filters
        expression = IPFabricFilterExpression.objects.create(
            name="Expression with Multiple Endpoints",
            expression=[{"siteName": ["eq", "Site1"]}],
        )
        expression.filters.add(filter1, filter2)

        # Create form with instance - should NOT set test_endpoint initial value
        form = IPFabricFilterExpressionForm(instance=expression)

        # Verify test_endpoint initial value is NOT set
        self.assertIsNone(form.fields["test_endpoint"].initial)

    def test_form_init_with_new_instance_does_not_set_initial(self):
        """Test that form __init__ does not set initial values for new instances"""
        # Create form without instance (new expression)
        form = IPFabricFilterExpressionForm()

        # Verify no initial values are set
        self.assertIsNone(form.fields["test_source"].initial)
        self.assertIsNone(form.fields["test_endpoint"].initial)
