"""Tests for services/manifest.py - semantic layer management service."""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import asdict

from services.auth import UserContext
from services.manifest import (
    ManifestStatus,
    ConflictItem,
    ManifestImportResult,
    get_manifest_status,
    list_semantic_models,
    get_semantic_model,
    list_metrics,
    get_metric,
    create_semantic_model,
    update_semantic_model,
    delete_semantic_model,
    create_metric,
    update_metric,
    delete_metric,
    import_manifest,
    export_manifest,
    preview_metric,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def admin_user() -> UserContext:
    """Admin user context for write operations."""
    return UserContext(
        uid="user123",
        email="admin@example.com",
        org_id="test-org",
        org_name="Test Org",
        role="admin",
    )


@pytest.fixture
def viewer_user() -> UserContext:
    """Viewer user context (read-only)."""
    return UserContext(
        uid="viewer456",
        email="viewer@example.com",
        org_id="test-org",
        org_name="Test Org",
        role="viewer",
    )


@pytest.fixture
def owner_user() -> UserContext:
    """Owner user context (full permissions)."""
    return UserContext(
        uid="owner789",
        email="owner@example.com",
        org_id="test-org",
        org_name="Test Org",
        role="owner",
    )


@pytest.fixture
def sample_manifest() -> dict:
    """Sample manifest with metrics and models."""
    return {
        "project_configuration": {"name": "test-project"},
        "metrics": [
            {
                "name": "revenue",
                "type": "simple",
                "description": "Total revenue",
                "_origin": "imported",
                "_imported_at": "2024-01-01T00:00:00Z",
                "_modified_at": "2024-01-02T00:00:00Z",
            },
            {
                "name": "orders",
                "type": "simple",
                "description": "Order count",
                "_origin": "metricly",
                "_imported_at": "2024-01-01T00:00:00Z",
            },
        ],
        "semantic_models": [
            {
                "name": "orders_model",
                "description": "Orders semantic model",
                "dimensions": [
                    {"name": "order_date"},
                    {"name": "customer_id"},
                ],
            },
            {
                "name": "products_model",
                "description": "Products model",
                "dimensions": [{"name": "product_id"}],
            },
        ],
    }


@pytest.fixture
def sample_model() -> dict:
    """Sample semantic model."""
    return {
        "name": "test_model",
        "description": "Test semantic model",
        "dimensions": [{"name": "dim1"}, {"name": "dim2"}],
        "measures": [{"name": "measure1", "agg": "sum"}],
    }


@pytest.fixture
def sample_metric() -> dict:
    """Sample metric definition."""
    return {
        "name": "test_metric",
        "type": "simple",
        "description": "Test metric",
        "type_params": {"measure": "measure1"},
    }


# ============================================================================
# TestManifestStatus - dataclass creation
# ============================================================================


class TestManifestStatus:
    """Test ManifestStatus dataclass."""

    def test_creation_with_all_fields(self):
        """Test creating ManifestStatus with all fields."""
        status = ManifestStatus(
            org_id="test-org",
            project_name="my-project",
            metric_count=10,
            model_count=5,
            dimension_count=20,
            last_updated="2024-01-15T10:30:00Z",
        )

        assert status.org_id == "test-org"
        assert status.project_name == "my-project"
        assert status.metric_count == 10
        assert status.model_count == 5
        assert status.dimension_count == 20
        assert status.last_updated == "2024-01-15T10:30:00Z"

    def test_creation_with_none_values(self):
        """Test creating ManifestStatus with None optional fields."""
        status = ManifestStatus(
            org_id="test-org",
            project_name=None,
            metric_count=0,
            model_count=0,
            dimension_count=0,
            last_updated=None,
        )

        assert status.org_id == "test-org"
        assert status.project_name is None
        assert status.metric_count == 0
        assert status.last_updated is None


# ============================================================================
# TestConflictItem - dataclass creation
# ============================================================================


class TestConflictItem:
    """Test ConflictItem dataclass."""

    def test_creation_with_metric_type(self):
        """Test creating ConflictItem for a metric."""
        conflict = ConflictItem(
            name="revenue",
            type="metric",
            reason="modified_since_import",
        )

        assert conflict.name == "revenue"
        assert conflict.type == "metric"
        assert conflict.reason == "modified_since_import"

    def test_creation_with_model_type(self):
        """Test creating ConflictItem for a model."""
        conflict = ConflictItem(
            name="orders_model",
            type="model",
            reason="origin_metricly",
        )

        assert conflict.name == "orders_model"
        assert conflict.type == "model"
        assert conflict.reason == "origin_metricly"


# ============================================================================
# TestManifestImportResult - dataclass creation with defaults
# ============================================================================


class TestManifestImportResult:
    """Test ManifestImportResult dataclass."""

    def test_creation_with_defaults(self):
        """Test creating ManifestImportResult with default list fields."""
        result = ManifestImportResult(
            imported_metrics=5,
            imported_models=3,
            skipped_metrics=1,
            skipped_models=0,
        )

        assert result.imported_metrics == 5
        assert result.imported_models == 3
        assert result.skipped_metrics == 1
        assert result.skipped_models == 0
        assert result.conflicts == []
        assert result.orphaned == []

    def test_creation_with_conflicts_and_orphaned(self):
        """Test creating ManifestImportResult with conflicts and orphaned."""
        conflicts = [
            ConflictItem(name="metric1", type="metric", reason="modified_since_import")
        ]
        result = ManifestImportResult(
            imported_metrics=5,
            imported_models=3,
            skipped_metrics=1,
            skipped_models=0,
            conflicts=conflicts,
            orphaned=["old_metric"],
        )

        assert len(result.conflicts) == 1
        assert result.conflicts[0].name == "metric1"
        assert result.orphaned == ["old_metric"]

    def test_default_lists_are_independent(self):
        """Test that default lists are independent between instances."""
        result1 = ManifestImportResult(
            imported_metrics=1,
            imported_models=1,
            skipped_metrics=0,
            skipped_models=0,
        )
        result2 = ManifestImportResult(
            imported_metrics=2,
            imported_models=2,
            skipped_metrics=0,
            skipped_models=0,
        )

        result1.conflicts.append(
            ConflictItem(name="test", type="metric", reason="test")
        )

        assert len(result1.conflicts) == 1
        assert len(result2.conflicts) == 0


# ============================================================================
# TestGetManifestStatus - mock storage.get_manifest
# ============================================================================


class TestGetManifestStatus:
    """Test get_manifest_status function."""

    @pytest.mark.asyncio
    async def test_returns_empty_status_when_no_manifest(self, admin_user):
        """Test returning empty status when no manifest exists."""
        with patch("services.manifest.storage.get_manifest") as mock_get:
            mock_get.return_value = None

            status = await get_manifest_status(admin_user)

            assert status.org_id == "test-org"
            assert status.project_name is None
            assert status.metric_count == 0
            assert status.model_count == 0
            assert status.dimension_count == 0
            assert status.last_updated is None
            mock_get.assert_called_once_with("test-org")

    @pytest.mark.asyncio
    async def test_returns_correct_counts(self, admin_user, sample_manifest):
        """Test returning correct counts from manifest."""
        with patch("services.manifest.storage.get_manifest") as mock_get:
            mock_get.return_value = sample_manifest

            status = await get_manifest_status(admin_user)

            assert status.org_id == "test-org"
            assert status.project_name == "test-project"
            assert status.metric_count == 2
            assert status.model_count == 2
            # orders_model has 2 dimensions, products_model has 1
            assert status.dimension_count == 3
            # Should be latest _modified_at or _imported_at
            assert status.last_updated == "2024-01-02T00:00:00Z"

    @pytest.mark.asyncio
    async def test_counts_dimensions_from_all_models(self, admin_user):
        """Test that dimensions are counted from all semantic models."""
        manifest = {
            "project_configuration": {"name": "test"},
            "metrics": [],
            "semantic_models": [
                {"name": "m1", "dimensions": [{"name": "d1"}, {"name": "d2"}, {"name": "d3"}]},
                {"name": "m2", "dimensions": [{"name": "d4"}, {"name": "d5"}]},
                {"name": "m3", "dimensions": []},
            ],
        }

        with patch("services.manifest.storage.get_manifest") as mock_get:
            mock_get.return_value = manifest

            status = await get_manifest_status(admin_user)

            assert status.dimension_count == 5


# ============================================================================
# TestListSemanticModels - mock storage.list_semantic_models
# ============================================================================


class TestListSemanticModels:
    """Test list_semantic_models function."""

    @pytest.mark.asyncio
    async def test_returns_models_from_storage(self, admin_user):
        """Test that models are returned from storage."""
        models = [
            {"name": "model1", "description": "First model"},
            {"name": "model2", "description": "Second model"},
        ]

        with patch("services.manifest.storage.list_semantic_models") as mock_list:
            mock_list.return_value = models

            result = await list_semantic_models(admin_user)

            assert result == models
            mock_list.assert_called_once_with("test-org")

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_models(self, admin_user):
        """Test returning empty list when no models exist."""
        with patch("services.manifest.storage.list_semantic_models") as mock_list:
            mock_list.return_value = []

            result = await list_semantic_models(admin_user)

            assert result == []


# ============================================================================
# TestGetSemanticModel - found/not found cases
# ============================================================================


class TestGetSemanticModel:
    """Test get_semantic_model function."""

    @pytest.mark.asyncio
    async def test_returns_model_when_found(self, admin_user, sample_model):
        """Test returning model when it exists."""
        with patch("services.manifest.storage.get_semantic_model") as mock_get:
            mock_get.return_value = sample_model

            result = await get_semantic_model(admin_user, "test_model")

            assert result == sample_model
            mock_get.assert_called_once_with("test-org", "test_model")

    @pytest.mark.asyncio
    async def test_raises_when_model_not_found(self, admin_user):
        """Test raising ValueError when model not found."""
        with patch("services.manifest.storage.get_semantic_model") as mock_get:
            mock_get.return_value = None

            with pytest.raises(ValueError) as exc_info:
                await get_semantic_model(admin_user, "nonexistent")

            assert "Semantic model 'nonexistent' not found" in str(exc_info.value)


# ============================================================================
# TestListMetrics - mock storage.list_metrics
# ============================================================================


class TestListMetrics:
    """Test list_metrics function."""

    @pytest.mark.asyncio
    async def test_returns_metrics_from_storage(self, admin_user):
        """Test that metrics are returned from storage."""
        metrics = [
            {"name": "metric1", "type": "simple"},
            {"name": "metric2", "type": "derived"},
        ]

        with patch("services.manifest.storage.list_metrics") as mock_list:
            mock_list.return_value = metrics

            result = await list_metrics(admin_user)

            assert result == metrics
            mock_list.assert_called_once_with("test-org")

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_metrics(self, admin_user):
        """Test returning empty list when no metrics exist."""
        with patch("services.manifest.storage.list_metrics") as mock_list:
            mock_list.return_value = []

            result = await list_metrics(admin_user)

            assert result == []


# ============================================================================
# TestGetMetric - found/not found cases
# ============================================================================


class TestGetMetric:
    """Test get_metric function."""

    @pytest.mark.asyncio
    async def test_returns_metric_when_found(self, admin_user, sample_metric):
        """Test returning metric when it exists."""
        with patch("services.manifest.storage.get_metric") as mock_get:
            mock_get.return_value = sample_metric

            result = await get_metric(admin_user, "test_metric")

            assert result == sample_metric
            mock_get.assert_called_once_with("test-org", "test_metric")

    @pytest.mark.asyncio
    async def test_raises_when_metric_not_found(self, admin_user):
        """Test raising ValueError when metric not found."""
        with patch("services.manifest.storage.get_metric") as mock_get:
            mock_get.return_value = None

            with pytest.raises(ValueError) as exc_info:
                await get_metric(admin_user, "nonexistent")

            assert "Metric 'nonexistent' not found" in str(exc_info.value)


# ============================================================================
# TestCreateSemanticModel - role check, already exists, success
# ============================================================================


class TestCreateSemanticModel:
    """Test create_semantic_model function."""

    @pytest.mark.asyncio
    async def test_requires_admin_role(self, viewer_user, sample_model):
        """Test that viewer role cannot create models."""
        with pytest.raises(PermissionError) as exc_info:
            await create_semantic_model(viewer_user, sample_model)

        assert "Requires admin role" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_when_model_already_exists(self, admin_user, sample_model):
        """Test raising ValueError when model already exists."""
        with patch("services.manifest.storage.get_semantic_model") as mock_get:
            mock_get.return_value = sample_model

            with pytest.raises(ValueError) as exc_info:
                await create_semantic_model(admin_user, sample_model)

            assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_when_name_missing(self, admin_user):
        """Test raising ValueError when model has no name."""
        with pytest.raises(ValueError) as exc_info:
            await create_semantic_model(admin_user, {"description": "No name"})

        assert "must have a name" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_creates_model_with_provenance(self, admin_user, sample_model):
        """Test successful model creation with provenance."""
        with patch("services.manifest.storage.get_semantic_model") as mock_get, \
             patch("services.manifest.storage.save_semantic_model") as mock_save, \
             patch("warehouse.get_org_warehouse") as mock_warehouse:

            mock_get.return_value = None  # Model doesn't exist
            mock_save.return_value = {**sample_model, "_origin": "metricly"}
            mock_wh_instance = MagicMock()
            mock_warehouse.return_value = mock_wh_instance

            result = await create_semantic_model(admin_user, sample_model)

            # Check provenance was set
            call_args = mock_save.call_args
            saved_model = call_args[0][1]
            assert saved_model["_origin"] == "metricly"

            # Check cache was invalidated
            mock_wh_instance.invalidate.assert_called_once_with("test-org")

    @pytest.mark.asyncio
    async def test_owner_can_create_model(self, owner_user, sample_model):
        """Test that owner role can create models."""
        with patch("services.manifest.storage.get_semantic_model") as mock_get, \
             patch("services.manifest.storage.save_semantic_model") as mock_save, \
             patch("warehouse.get_org_warehouse") as mock_warehouse:

            mock_get.return_value = None
            mock_save.return_value = {**sample_model, "_origin": "metricly"}
            mock_warehouse.return_value = MagicMock()

            result = await create_semantic_model(owner_user, sample_model)

            mock_save.assert_called_once()


# ============================================================================
# TestUpdateSemanticModel - role check, not found, success
# ============================================================================


class TestUpdateSemanticModel:
    """Test update_semantic_model function."""

    @pytest.mark.asyncio
    async def test_requires_admin_role(self, viewer_user):
        """Test that viewer role cannot update models."""
        with pytest.raises(PermissionError) as exc_info:
            await update_semantic_model(viewer_user, "test_model", {"description": "new"})

        assert "Requires admin role" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_when_model_not_found(self, admin_user):
        """Test raising ValueError when model not found."""
        with patch("services.manifest.storage.get_semantic_model") as mock_get:
            mock_get.return_value = None

            with pytest.raises(ValueError) as exc_info:
                await update_semantic_model(admin_user, "nonexistent", {"description": "new"})

            assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_updates_model_successfully(self, admin_user, sample_model):
        """Test successful model update."""
        with patch("services.manifest.storage.get_semantic_model") as mock_get, \
             patch("services.manifest.storage.save_semantic_model") as mock_save, \
             patch("warehouse.get_org_warehouse") as mock_warehouse:

            mock_get.return_value = sample_model
            updated_model = {**sample_model, "description": "Updated description"}
            mock_save.return_value = updated_model
            mock_warehouse.return_value = MagicMock()

            result = await update_semantic_model(
                admin_user, "test_model", {"description": "Updated description"}
            )

            mock_save.assert_called_once()
            # Verify name cannot be changed
            saved_model = mock_save.call_args[0][1]
            assert saved_model["name"] == "test_model"

    @pytest.mark.asyncio
    async def test_prevents_name_change(self, admin_user, sample_model):
        """Test that model name cannot be changed via update."""
        with patch("services.manifest.storage.get_semantic_model") as mock_get, \
             patch("services.manifest.storage.save_semantic_model") as mock_save, \
             patch("warehouse.get_org_warehouse") as mock_warehouse:

            mock_get.return_value = sample_model
            mock_save.return_value = sample_model
            mock_warehouse.return_value = MagicMock()

            await update_semantic_model(
                admin_user, "test_model", {"name": "new_name", "description": "new"}
            )

            saved_model = mock_save.call_args[0][1]
            assert saved_model["name"] == "test_model"  # Original name preserved


# ============================================================================
# TestDeleteSemanticModel - role check, not found, success
# ============================================================================


class TestDeleteSemanticModel:
    """Test delete_semantic_model function."""

    @pytest.mark.asyncio
    async def test_requires_admin_role(self, viewer_user):
        """Test that viewer role cannot delete models."""
        with pytest.raises(PermissionError) as exc_info:
            await delete_semantic_model(viewer_user, "test_model")

        assert "Requires admin role" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_when_model_not_found(self, admin_user):
        """Test raising ValueError when model not found."""
        with patch("services.manifest.storage.get_semantic_model") as mock_get:
            mock_get.return_value = None

            with pytest.raises(ValueError) as exc_info:
                await delete_semantic_model(admin_user, "nonexistent")

            assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_deletes_model_successfully(self, admin_user, sample_model):
        """Test successful model deletion."""
        with patch("services.manifest.storage.get_semantic_model") as mock_get, \
             patch("services.manifest.storage.delete_semantic_model") as mock_delete, \
             patch("warehouse.get_org_warehouse") as mock_warehouse:

            mock_get.return_value = sample_model
            mock_warehouse.return_value = MagicMock()

            result = await delete_semantic_model(admin_user, "test_model")

            assert result is True
            mock_delete.assert_called_once_with("test-org", "test_model")


# ============================================================================
# TestCreateMetric - role check, already exists, success
# ============================================================================


class TestCreateMetric:
    """Test create_metric function."""

    @pytest.mark.asyncio
    async def test_requires_admin_role(self, viewer_user, sample_metric):
        """Test that viewer role cannot create metrics."""
        with pytest.raises(PermissionError) as exc_info:
            await create_metric(viewer_user, sample_metric)

        assert "Requires admin role" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_when_metric_already_exists(self, admin_user, sample_metric):
        """Test raising ValueError when metric already exists."""
        with patch("services.manifest.storage.get_metric") as mock_get:
            mock_get.return_value = sample_metric

            with pytest.raises(ValueError) as exc_info:
                await create_metric(admin_user, sample_metric)

            assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_when_name_missing(self, admin_user):
        """Test raising ValueError when metric has no name."""
        with pytest.raises(ValueError) as exc_info:
            await create_metric(admin_user, {"type": "simple"})

        assert "must have a name" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_creates_metric_with_provenance(self, admin_user, sample_metric):
        """Test successful metric creation with provenance."""
        with patch("services.manifest.storage.get_metric") as mock_get, \
             patch("services.manifest.storage.create_metric") as mock_create, \
             patch("warehouse.get_org_warehouse") as mock_warehouse:

            mock_get.return_value = None  # Metric doesn't exist
            mock_create.return_value = {**sample_metric, "_origin": "metricly"}
            mock_warehouse.return_value = MagicMock()

            result = await create_metric(admin_user, sample_metric)

            # Check provenance was set
            call_args = mock_create.call_args
            created_metric = call_args[0][1]
            assert created_metric["_origin"] == "metricly"

    @pytest.mark.asyncio
    async def test_owner_can_create_metric(self, owner_user, sample_metric):
        """Test that owner role can create metrics."""
        with patch("services.manifest.storage.get_metric") as mock_get, \
             patch("services.manifest.storage.create_metric") as mock_create, \
             patch("warehouse.get_org_warehouse") as mock_warehouse:

            mock_get.return_value = None
            mock_create.return_value = sample_metric
            mock_warehouse.return_value = MagicMock()

            await create_metric(owner_user, sample_metric)

            mock_create.assert_called_once()


# ============================================================================
# TestUpdateMetric - role check, not found, success
# ============================================================================


class TestUpdateMetric:
    """Test update_metric function."""

    @pytest.mark.asyncio
    async def test_requires_admin_role(self, viewer_user):
        """Test that viewer role cannot update metrics."""
        with pytest.raises(PermissionError) as exc_info:
            await update_metric(viewer_user, "test_metric", {"description": "new"})

        assert "Requires admin role" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_when_metric_not_found(self, admin_user):
        """Test raising ValueError when metric not found."""
        with patch("services.manifest.storage.get_metric") as mock_get:
            mock_get.return_value = None

            with pytest.raises(ValueError) as exc_info:
                await update_metric(admin_user, "nonexistent", {"description": "new"})

            assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_updates_metric_successfully(self, admin_user, sample_metric):
        """Test successful metric update."""
        with patch("services.manifest.storage.get_metric") as mock_get, \
             patch("services.manifest.storage.update_metric") as mock_update, \
             patch("warehouse.get_org_warehouse") as mock_warehouse:

            mock_get.return_value = sample_metric
            updated_metric = {**sample_metric, "description": "Updated"}
            mock_update.return_value = updated_metric
            mock_warehouse.return_value = MagicMock()

            result = await update_metric(
                admin_user, "test_metric", {"description": "Updated"}
            )

            mock_update.assert_called_once_with(
                "test-org", "test_metric", {"description": "Updated"}, "user123"
            )


# ============================================================================
# TestDeleteMetric - role check, not found, success
# ============================================================================


class TestDeleteMetric:
    """Test delete_metric function."""

    @pytest.mark.asyncio
    async def test_requires_admin_role(self, viewer_user):
        """Test that viewer role cannot delete metrics."""
        with pytest.raises(PermissionError) as exc_info:
            await delete_metric(viewer_user, "test_metric")

        assert "Requires admin role" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_when_metric_not_found(self, admin_user):
        """Test raising ValueError when metric not found."""
        with patch("services.manifest.storage.get_metric") as mock_get:
            mock_get.return_value = None

            with pytest.raises(ValueError) as exc_info:
                await delete_metric(admin_user, "nonexistent")

            assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_deletes_metric_successfully(self, admin_user, sample_metric):
        """Test successful metric deletion."""
        with patch("services.manifest.storage.get_metric") as mock_get, \
             patch("services.manifest.storage.delete_metric") as mock_delete, \
             patch("warehouse.get_org_warehouse") as mock_warehouse:

            mock_get.return_value = sample_metric
            mock_warehouse.return_value = MagicMock()

            result = await delete_metric(admin_user, "test_metric")

            assert result is True
            mock_delete.assert_called_once_with("test-org", "test_metric")


# ============================================================================
# TestImportManifest - role check, conflicts without force, conflicts with force, success
# ============================================================================


class TestImportManifest:
    """Test import_manifest function."""

    @pytest.mark.asyncio
    async def test_requires_admin_role(self, viewer_user, sample_manifest):
        """Test that viewer role cannot import manifest."""
        with pytest.raises(PermissionError) as exc_info:
            await import_manifest(viewer_user, sample_manifest)

        assert "Requires admin role" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_when_manifest_empty(self, admin_user):
        """Test raising ValueError when manifest has no content."""
        with pytest.raises(ValueError) as exc_info:
            await import_manifest(admin_user, {})

        assert "must contain" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_on_conflicts_without_force(self, admin_user):
        """Test raising ValueError when conflicts exist and force=False."""
        with patch("services.manifest.storage.import_manifest") as mock_import, \
             patch("warehouse.get_org_warehouse") as mock_warehouse:

            # Match the nested structure returned by storage.import_manifest
            mock_import.return_value = {
                "semantic_models": {
                    "imported": 2,
                    "updated": 0,
                    "skipped": 1,
                    "conflicts": ["orders_model"],
                },
                "metrics": {
                    "imported": 5,
                    "updated": 0,
                    "skipped": 2,
                    "conflicts": ["revenue"],
                },
                "orphaned": {
                    "semantic_models": [],
                    "metrics": [],
                },
            }

            manifest_data = {"metrics": [{"name": "test"}]}

            with pytest.raises(ValueError) as exc_info:
                await import_manifest(admin_user, manifest_data, force=False)

            assert "forked items would be overwritten" in str(exc_info.value)
            assert "revenue" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_succeeds_with_force_on_conflicts(self, admin_user):
        """Test that import succeeds with force=True even with conflicts."""
        with patch("services.manifest.storage.import_manifest") as mock_import, \
             patch("warehouse.get_org_warehouse") as mock_warehouse:

            # Match the nested structure returned by storage.import_manifest
            mock_import.return_value = {
                "semantic_models": {
                    "imported": 2,
                    "updated": 0,
                    "skipped": 0,
                    "conflicts": [],
                },
                "metrics": {
                    "imported": 5,
                    "updated": 0,
                    "skipped": 0,
                    "conflicts": ["revenue"],
                },
                "orphaned": {
                    "semantic_models": [],
                    "metrics": [],
                },
            }
            mock_warehouse.return_value = MagicMock()

            manifest_data = {"metrics": [{"name": "test"}]}

            result = await import_manifest(admin_user, manifest_data, force=True)

            assert result.imported_metrics == 5
            assert len(result.conflicts) == 1
            assert result.conflicts[0].name == "revenue"

    @pytest.mark.asyncio
    async def test_successful_import_without_conflicts(self, admin_user):
        """Test successful import with no conflicts."""
        with patch("services.manifest.storage.import_manifest") as mock_import, \
             patch("warehouse.get_org_warehouse") as mock_warehouse:

            # Match the nested structure returned by storage.import_manifest
            mock_import.return_value = {
                "semantic_models": {
                    "imported": 5,
                    "updated": 0,
                    "skipped": 0,
                    "conflicts": [],
                },
                "metrics": {
                    "imported": 10,
                    "updated": 0,
                    "skipped": 0,
                    "conflicts": [],
                },
                "orphaned": {
                    "semantic_models": [],
                    "metrics": ["old_metric"],
                },
            }
            mock_warehouse.return_value = MagicMock()

            manifest_data = {"metrics": [{"name": "m1"}], "semantic_models": [{"name": "s1"}]}

            result = await import_manifest(admin_user, manifest_data)

            assert result.imported_metrics == 10
            assert result.imported_models == 5
            assert result.skipped_metrics == 0
            assert len(result.conflicts) == 0
            assert result.orphaned == ["old_metric"]

    @pytest.mark.asyncio
    async def test_invalidates_cache_after_import(self, admin_user):
        """Test that cache is invalidated after successful import."""
        with patch("services.manifest.storage.import_manifest") as mock_import, \
             patch("warehouse.get_org_warehouse") as mock_warehouse:

            # Match the nested structure returned by storage.import_manifest
            mock_import.return_value = {
                "semantic_models": {
                    "imported": 1,
                    "updated": 0,
                    "skipped": 0,
                    "conflicts": [],
                },
                "metrics": {
                    "imported": 1,
                    "updated": 0,
                    "skipped": 0,
                    "conflicts": [],
                },
                "orphaned": {
                    "semantic_models": [],
                    "metrics": [],
                },
            }
            mock_wh_instance = MagicMock()
            mock_warehouse.return_value = mock_wh_instance

            await import_manifest(admin_user, {"metrics": [{"name": "test"}]})

            mock_wh_instance.invalidate.assert_called_once_with("test-org")


# ============================================================================
# TestExportManifest - strips provenance fields
# ============================================================================


class TestExportManifest:
    """Test export_manifest function."""

    @pytest.mark.asyncio
    async def test_returns_empty_manifest_when_none_exists(self, admin_user):
        """Test returning empty manifest when none exists."""
        with patch("services.manifest.storage.get_manifest") as mock_get:
            mock_get.return_value = None

            result = await export_manifest(admin_user)

            assert result == {
                "metrics": [],
                "semantic_models": [],
                "project_configuration": {},
            }

    @pytest.mark.asyncio
    async def test_strips_provenance_fields(self, admin_user, sample_manifest):
        """Test that provenance fields (starting with _) are stripped."""
        with patch("services.manifest.storage.get_manifest") as mock_get:
            mock_get.return_value = sample_manifest

            result = await export_manifest(admin_user)

            # Check metrics have no _ fields
            for metric in result["metrics"]:
                assert not any(k.startswith("_") for k in metric.keys())
                assert "name" in metric  # Regular fields preserved

            # Check models have no _ fields
            for model in result["semantic_models"]:
                assert not any(k.startswith("_") for k in model.keys())

    @pytest.mark.asyncio
    async def test_preserves_project_configuration(self, admin_user, sample_manifest):
        """Test that project_configuration is preserved."""
        with patch("services.manifest.storage.get_manifest") as mock_get:
            mock_get.return_value = sample_manifest

            result = await export_manifest(admin_user)

            assert result["project_configuration"] == {"name": "test-project"}

    @pytest.mark.asyncio
    async def test_viewer_can_export(self, viewer_user, sample_manifest):
        """Test that even viewer can export manifest (read operation)."""
        with patch("services.manifest.storage.get_manifest") as mock_get:
            mock_get.return_value = sample_manifest

            result = await export_manifest(viewer_user)

            assert len(result["metrics"]) == 2


# ============================================================================
# TestPreviewMetric - success case (mock complex preview)
# ============================================================================


class TestPreviewMetric:
    """Test preview_metric function."""

    @pytest.mark.asyncio
    async def test_returns_error_when_no_name(self, admin_user):
        """Test returning error when metric has no name."""
        result = await preview_metric(admin_user, {"type": "simple"})

        assert "error" in result
        assert "must have a name" in result["error"]

    @pytest.mark.asyncio
    async def test_returns_error_when_no_manifest(self, admin_user, sample_metric):
        """Test returning error when org has no manifest."""
        with patch("services.manifest.storage.get_manifest") as mock_get:
            mock_get.return_value = None

            result = await preview_metric(admin_user, sample_metric)

            assert "error" in result
            assert "No manifest found" in result["error"]

    @pytest.mark.asyncio
    async def test_successful_preview_with_defaults(self, admin_user, sample_metric, sample_manifest):
        """Test successful metric preview with default query params."""
        import pandas as pd

        with patch("services.manifest.storage.get_manifest") as mock_get_manifest, \
             patch("warehouse.get_org_warehouse") as mock_warehouse:

            mock_get_manifest.return_value = sample_manifest

            # Mock the engine and query result
            mock_engine = MagicMock()
            mock_query_result = MagicMock()
            mock_query_result.exception = None
            mock_query_result.df = pd.DataFrame({
                "metric_time__day": ["2024-01-01", "2024-01-02"],
                "test_metric": [100, 200],
            })
            mock_engine.query.return_value = mock_query_result

            mock_wh_instance = MagicMock()
            mock_wh_instance.build_temp_engine.return_value = mock_engine
            mock_warehouse.return_value = mock_wh_instance

            result = await preview_metric(admin_user, sample_metric)

            assert result["success"] is True
            assert len(result["data"]) == 2
            assert "metric_time__day" in result["columns"]
            assert result["row_count"] == 2

    @pytest.mark.asyncio
    async def test_preview_with_custom_query(self, admin_user, sample_metric, sample_manifest):
        """Test metric preview with custom sample query parameters."""
        import pandas as pd

        with patch("services.manifest.storage.get_manifest") as mock_get_manifest, \
             patch("warehouse.get_org_warehouse") as mock_warehouse:

            mock_get_manifest.return_value = sample_manifest

            mock_engine = MagicMock()
            mock_query_result = MagicMock()
            mock_query_result.exception = None
            mock_query_result.df = pd.DataFrame({
                "metric_time__month": ["2024-01"],
                "test_metric": [500],
            })
            mock_engine.query.return_value = mock_query_result

            mock_wh_instance = MagicMock()
            mock_wh_instance.build_temp_engine.return_value = mock_engine
            mock_warehouse.return_value = mock_wh_instance

            custom_query = {
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "grain": "month",
                "limit": 10,
            }

            result = await preview_metric(admin_user, sample_metric, sample_query=custom_query)

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_returns_error_on_query_exception(self, admin_user, sample_metric, sample_manifest):
        """Test returning error when query fails."""
        with patch("services.manifest.storage.get_manifest") as mock_get_manifest, \
             patch("warehouse.get_org_warehouse") as mock_warehouse:

            mock_get_manifest.return_value = sample_manifest

            mock_engine = MagicMock()
            mock_query_result = MagicMock()
            mock_query_result.exception = ValueError("Invalid metric reference")
            mock_engine.query.return_value = mock_query_result

            mock_wh_instance = MagicMock()
            mock_wh_instance.build_temp_engine.return_value = mock_engine
            mock_warehouse.return_value = mock_wh_instance

            result = await preview_metric(admin_user, sample_metric)

            assert "error" in result
            assert "Invalid metric reference" in result["error"]

    @pytest.mark.asyncio
    async def test_replaces_existing_metric_in_temp_manifest(self, admin_user, sample_manifest):
        """Test that preview replaces existing metric with same name in temp manifest."""
        import pandas as pd

        # Metric with name that already exists in sample_manifest
        updated_metric = {
            "name": "revenue",  # Exists in sample_manifest
            "type": "derived",  # Changed type
            "description": "Updated revenue calculation",
        }

        with patch("services.manifest.storage.get_manifest") as mock_get_manifest, \
             patch("warehouse.get_org_warehouse") as mock_warehouse:

            mock_get_manifest.return_value = sample_manifest

            mock_engine = MagicMock()
            mock_query_result = MagicMock()
            mock_query_result.exception = None
            mock_query_result.df = pd.DataFrame({"revenue": [1000]})
            mock_engine.query.return_value = mock_query_result

            mock_wh_instance = MagicMock()
            mock_wh_instance.build_temp_engine.return_value = mock_engine
            mock_warehouse.return_value = mock_wh_instance

            result = await preview_metric(admin_user, updated_metric)

            # Verify build_temp_engine was called with modified manifest
            call_args = mock_wh_instance.build_temp_engine.call_args
            temp_manifest = call_args[0][1]

            # Should have only one 'revenue' metric (the preview one, not the original)
            revenue_metrics = [m for m in temp_manifest["metrics"] if m.get("name") == "revenue"]
            assert len(revenue_metrics) == 1
            assert revenue_metrics[0]["type"] == "derived"
