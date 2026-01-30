"""Quick metrics expression parser and CRUD operations.

Quick metrics are user-defined derived metrics that combine base metrics
with arithmetic expressions, e.g., "total_revenue / order_count" for
average order value.

Features:
- Expression parsing using Python's ast module for safe evaluation
- CRUD operations for storing quick metrics in Firestore
- Validation against manifest metrics
- qm: prefix for referencing quick metrics (e.g., qm:revenue_per_order)

Security:
- Uses Python's ast module for safe parsing (no eval)
- Only allows identifiers, numbers, and arithmetic operators
- No function calls, attribute access, or other Python features
- Whitelist approach using ast.NodeVisitor

Note: Requires Python 3.8+ (uses ast.Constant instead of deprecated ast.Num)
"""

import ast
import re
import uuid
from datetime import datetime, UTC
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from google.cloud import firestore


# ============================================================================
# Pydantic Models
# ============================================================================


class ParsedExpression(BaseModel):
    """Result of parsing a quick metric expression."""

    expression: str = Field(description="Original expression string")
    base_metrics: list[str] = Field(
        description="Metric names referenced in the expression"
    )
    ast_tree: dict = Field(
        description="Serialized AST for evaluation (JSON-serializable)"
    )


class QuickMetric(BaseModel):
    """A user-defined derived metric."""

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() + "Z" if v.tzinfo is None else v.isoformat()
        }
    )

    id: str = Field(description="Unique identifier")
    org_id: str = Field(description="Organization ID")
    created_by: str = Field(description="User ID who created the metric")
    name: str = Field(description="Metric name (stored without qm: prefix)")
    description: str | None = Field(default=None, description="Optional description")
    expression: str = Field(description="Arithmetic expression, e.g., 'total_revenue / order_count'")
    base_metrics: list[str] = Field(description="Metric names extracted from expression")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class QuickMetricSummary(BaseModel):
    """Lightweight quick metric for listing."""

    id: str = Field(description="Unique identifier")
    name: str = Field(description="Metric name (without qm: prefix)")
    description: str | None = Field(default=None, description="Optional description")
    expression: str = Field(description="Arithmetic expression")


# ============================================================================
# Exceptions
# ============================================================================


class ExpressionError(Exception):
    """Invalid expression error with details."""

    def __init__(self, message: str, position: int | None = None):
        self.message = message
        self.position = position
        super().__init__(message)


# ============================================================================
# AST Validation (Security)
# ============================================================================

# Allowed AST node types for safe expressions
ALLOWED_NODE_TYPES: set[type] = {
    ast.Expression,  # Root node for expressions
    ast.BinOp,  # Binary operations (a + b)
    ast.UnaryOp,  # Unary operations (-a)
    ast.Constant,  # Numbers (Python 3.8+)
    ast.Name,  # Variable names (metric references)
    ast.Load,  # Load context for names
    ast.Add,  # +
    ast.Sub,  # -
    ast.Mult,  # *
    ast.Div,  # /
    ast.USub,  # Unary minus
    ast.UAdd,  # Unary plus
}


class SafeExpressionVisitor(ast.NodeVisitor):
    """Validates that an AST only contains safe, allowed nodes.

    Ensures expressions contain only:
    - Identifiers (metric names)
    - Numbers (int, float)
    - Arithmetic operators (+, -, *, /)
    - Parentheses (implicit in AST structure)
    """

    def __init__(self):
        self.metrics: list[str] = []
        self.errors: list[str] = []

    def generic_visit(self, node: ast.AST) -> None:
        """Check if node type is allowed."""
        if type(node) not in ALLOWED_NODE_TYPES:
            node_name = type(node).__name__
            self.errors.append(f"Disallowed expression element: {node_name}")
        super().generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Collect metric names from identifier nodes."""
        # Validate metric name format (alphanumeric + underscore, starts with letter)
        name = node.id
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
            self.errors.append(f"Invalid metric name: {name}")
        else:
            if name not in self.metrics:
                self.metrics.append(name)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        """Validate constant values are numbers only."""
        if not isinstance(node.value, (int, float)):
            self.errors.append(f"Only numeric constants allowed, got: {type(node.value).__name__}")
        self.generic_visit(node)


# ============================================================================
# AST Serialization
# ============================================================================


def _serialize_ast(node: ast.AST) -> dict[str, Any]:
    """Serialize an AST node to a JSON-serializable dict.

    Args:
        node: AST node to serialize

    Returns:
        Dictionary representation of the node
    """
    if isinstance(node, ast.Expression):
        return {"type": "Expression", "body": _serialize_ast(node.body)}

    elif isinstance(node, ast.BinOp):
        op_map = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
        }
        return {
            "type": "BinOp",
            "op": op_map.get(type(node.op), str(type(node.op).__name__)),
            "left": _serialize_ast(node.left),
            "right": _serialize_ast(node.right),
        }

    elif isinstance(node, ast.UnaryOp):
        op_map = {
            ast.USub: "-",
            ast.UAdd: "+",
        }
        return {
            "type": "UnaryOp",
            "op": op_map.get(type(node.op), str(type(node.op).__name__)),
            "operand": _serialize_ast(node.operand),
        }

    elif isinstance(node, ast.Constant):
        return {"type": "Constant", "value": node.value}

    elif isinstance(node, ast.Name):
        return {"type": "Name", "id": node.id}

    else:
        raise ExpressionError(f"Cannot serialize node type: {type(node).__name__}")


# ============================================================================
# Public Functions
# ============================================================================


def parse_expression(expression: str) -> ParsedExpression:
    """Parse and validate a quick metric expression.

    Parses arithmetic expressions like "revenue / orders" or
    "(total_revenue - cogs) / total_revenue * 100" and extracts
    the referenced metric names.

    Args:
        expression: Arithmetic expression string

    Returns:
        ParsedExpression with base_metrics and serialized AST

    Raises:
        ExpressionError: If expression is invalid or contains disallowed elements

    Examples:
        >>> result = parse_expression("revenue / orders")
        >>> result.base_metrics
        ['revenue', 'orders']

        >>> result = parse_expression("(total_revenue - cogs) / total_revenue * 100")
        >>> result.base_metrics
        ['total_revenue', 'cogs']
    """
    if not expression or not expression.strip():
        raise ExpressionError("Expression cannot be empty")

    expression = expression.strip()

    # Parse the expression into an AST
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise ExpressionError(
            f"Syntax error: {e.msg}",
            position=e.offset,
        )

    # Validate the AST for safety
    visitor = SafeExpressionVisitor()
    visitor.visit(tree)

    if visitor.errors:
        raise ExpressionError("; ".join(visitor.errors))

    if not visitor.metrics:
        raise ExpressionError(
            "Expression must reference at least one metric"
        )

    # Serialize the AST
    ast_dict = _serialize_ast(tree)

    return ParsedExpression(
        expression=expression,
        base_metrics=visitor.metrics,
        ast_tree=ast_dict,
    )


def evaluate_expression(
    parsed: ParsedExpression,
    metric_values: dict[str, float],
) -> float:
    """Evaluate a parsed expression with concrete metric values.

    Args:
        parsed: Previously parsed expression
        metric_values: Map of metric name to its value

    Returns:
        Computed result as float

    Raises:
        ExpressionError: If metric value missing or division by zero

    Examples:
        >>> parsed = parse_expression("revenue / orders")
        >>> evaluate_expression(parsed, {"revenue": 1000.0, "orders": 100.0})
        10.0
    """
    # Check all required metrics are provided
    missing = [m for m in parsed.base_metrics if m not in metric_values]
    if missing:
        raise ExpressionError(
            f"Missing metric values: {', '.join(missing)}"
        )

    def _eval_node(node: dict) -> float:
        """Recursively evaluate a serialized AST node."""
        node_type = node["type"]

        if node_type == "Expression":
            return _eval_node(node["body"])

        elif node_type == "Constant":
            return float(node["value"])

        elif node_type == "Name":
            return float(metric_values[node["id"]])

        elif node_type == "UnaryOp":
            operand = _eval_node(node["operand"])
            op = node["op"]
            if op == "-":
                return -operand
            elif op == "+":
                return operand
            else:
                raise ExpressionError(f"Unknown unary operator: {op}")

        elif node_type == "BinOp":
            left = _eval_node(node["left"])
            right = _eval_node(node["right"])
            op = node["op"]

            if op == "+":
                return left + right
            elif op == "-":
                return left - right
            elif op == "*":
                return left * right
            elif op == "/":
                if right == 0:
                    raise ExpressionError("Division by zero")
                return left / right
            else:
                raise ExpressionError(f"Unknown operator: {op}")

        else:
            raise ExpressionError(f"Unknown node type: {node_type}")

    return _eval_node(parsed.ast_tree)


def validate_metrics_exist(
    base_metrics: list[str],
    available_metrics: list[str],
) -> list[str]:
    """Check that all referenced metrics exist in available metrics.

    Args:
        base_metrics: List of metric names from parsed expression
        available_metrics: List of available metric names

    Returns:
        List of missing metric names (empty if all valid)

    Examples:
        >>> validate_metrics_exist(["revenue", "orders"], ["revenue", "orders", "cogs"])
        []
        >>> validate_metrics_exist(["revenue", "unknown"], ["revenue", "orders"])
        ['unknown']
    """
    available_set = set(available_metrics)
    return [m for m in base_metrics if m not in available_set]


# ============================================================================
# Firestore Access
# ============================================================================

_firestore_client = None


def _get_firestore_client() -> firestore.Client:
    """Get or create Firestore client."""
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = firestore.Client(project="metricly-dev")
    return _firestore_client


def _serialize_firestore_doc(data: dict) -> dict:
    """Convert Firestore document to JSON-serializable dict."""
    from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds

    result = {}
    for key, value in data.items():
        if isinstance(value, DatetimeWithNanoseconds):
            result[key] = value
        elif isinstance(value, datetime):
            result[key] = value
        elif isinstance(value, dict):
            result[key] = _serialize_firestore_doc(value)
        elif isinstance(value, list):
            result[key] = [
                _serialize_firestore_doc(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


# ============================================================================
# Quick Metric CRUD Operations
# ============================================================================

# Import here to avoid circular imports
from services.auth import UserContext


async def create_quick_metric(
    user: UserContext,
    name: str,
    expression: str,
    description: str | None = None,
) -> QuickMetric:
    """Create a new quick metric.

    Validates:
    - Name is valid identifier (alphanumeric + underscore, starts with letter)
    - Name doesn't conflict with existing manifest metrics
    - Expression parses correctly
    - Base metrics all exist in manifest

    Args:
        user: Authenticated user context
        name: Metric name (without qm: prefix)
        expression: Arithmetic expression
        description: Optional description

    Returns:
        Created QuickMetric

    Raises:
        ValueError: If validation fails
        ExpressionError: If expression is invalid
    """
    import storage

    # Validate name format (must start with letter, alphanumeric + underscore)
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", name):
        raise ValueError(
            f"Invalid metric name '{name}'. Must start with a letter and contain only "
            "letters, numbers, and underscores."
        )

    # Check for conflict with existing manifest metrics
    manifest_metrics = storage.list_metrics(user.org_id)
    manifest_metric_names = {m.get("name") for m in manifest_metrics}
    if name in manifest_metric_names:
        raise ValueError(
            f"Name '{name}' conflicts with an existing manifest metric. "
            "Choose a different name."
        )

    # Parse expression (validates syntax and extracts base metrics)
    parsed = parse_expression(expression)

    # Validate that all base metrics exist in the manifest
    missing = validate_metrics_exist(parsed.base_metrics, list(manifest_metric_names))
    if missing:
        raise ValueError(
            f"Expression references unknown metrics: {', '.join(missing)}. "
            "All referenced metrics must exist in the manifest."
        )

    db = _get_firestore_client()
    qm_ref = db.collection("organizations").document(user.org_id).collection("quick_metrics")

    # Check if name already exists as a quick metric
    existing = list(qm_ref.where("name", "==", name).limit(1).stream())
    if existing:
        raise ValueError(f"Quick metric with name '{name}' already exists")

    now = datetime.now(UTC)
    metric_id = str(uuid.uuid4())

    metric_data = {
        "name": name,
        "expression": expression,
        "description": description,
        "base_metrics": parsed.base_metrics,
        "created_by": user.uid,
        "created_at": now,
        "updated_at": now,
    }

    doc_ref = qm_ref.document(metric_id)
    doc_ref.set(metric_data)

    return QuickMetric(
        id=metric_id,
        org_id=user.org_id,
        **metric_data,
    )


async def list_quick_metrics(user: UserContext) -> list[QuickMetricSummary]:
    """List all quick metrics for the organization.

    Args:
        user: Authenticated user context

    Returns:
        List of QuickMetricSummary objects
    """
    db = _get_firestore_client()
    qm_ref = db.collection("organizations").document(user.org_id).collection("quick_metrics")

    result = []
    for doc in qm_ref.stream():
        data = _serialize_firestore_doc(doc.to_dict())
        result.append(QuickMetricSummary(
            id=doc.id,
            name=data["name"],
            description=data.get("description"),
            expression=data["expression"],
        ))

    # Sort by name for consistent ordering
    result.sort(key=lambda m: m.name)
    return result


async def get_quick_metric(user: UserContext, metric_id: str) -> QuickMetric:
    """Get a quick metric by ID.

    Args:
        user: Authenticated user context
        metric_id: Quick metric ID

    Returns:
        QuickMetric object

    Raises:
        ValueError: If metric not found
    """
    db = _get_firestore_client()
    doc_ref = db.collection("organizations").document(user.org_id).collection("quick_metrics").document(metric_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise ValueError(f"Quick metric with ID '{metric_id}' not found")

    data = _serialize_firestore_doc(doc.to_dict())
    data["id"] = doc.id
    data["org_id"] = user.org_id
    return QuickMetric.model_validate(data)


async def get_quick_metric_by_name(user: UserContext, name: str) -> QuickMetric | None:
    """Get a quick metric by name (without qm: prefix).

    This is the primary lookup method for query integration,
    where metrics are referenced by qm:name syntax.

    Args:
        user: Authenticated user context
        name: Metric name (without qm: prefix)

    Returns:
        QuickMetric object or None if not found
    """
    db = _get_firestore_client()
    qm_ref = db.collection("organizations").document(user.org_id).collection("quick_metrics")

    # Query by name
    docs = list(qm_ref.where("name", "==", name).limit(1).stream())

    if not docs:
        return None

    doc = docs[0]
    data = _serialize_firestore_doc(doc.to_dict())
    data["id"] = doc.id
    data["org_id"] = user.org_id

    return QuickMetric.model_validate(data)


async def update_quick_metric(
    user: UserContext,
    metric_id: str,
    name: str | None = None,
    expression: str | None = None,
    description: str | None = None,
) -> QuickMetric:
    """Update a quick metric.

    Args:
        user: Authenticated user context
        metric_id: Quick metric ID to update
        name: New name (optional)
        expression: New expression (optional)
        description: New description (optional, use empty string to clear)

    Returns:
        Updated QuickMetric

    Raises:
        ValueError: If metric not found or validation fails
        ExpressionError: If new expression is invalid
    """
    import storage

    db = _get_firestore_client()
    doc_ref = db.collection("organizations").document(user.org_id).collection("quick_metrics").document(metric_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise ValueError(f"Quick metric with ID '{metric_id}' not found")

    data = doc.to_dict()
    updates: dict[str, Any] = {"updated_at": datetime.now(UTC)}

    # Validate and update name if provided
    if name is not None and name != data.get("name"):
        # Validate name format
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", name):
            raise ValueError(
                f"Invalid metric name '{name}'. Must start with a letter and contain only "
                "letters, numbers, and underscores."
            )

        # Check for conflict with manifest metrics
        manifest_metrics = storage.list_metrics(user.org_id)
        manifest_metric_names = {m.get("name") for m in manifest_metrics}
        if name in manifest_metric_names:
            raise ValueError(
                f"Name '{name}' conflicts with an existing manifest metric."
            )

        # Check if new name already exists on a different quick metric
        qm_ref = db.collection("organizations").document(user.org_id).collection("quick_metrics")
        existing = list(qm_ref.where("name", "==", name).limit(1).stream())
        if existing and existing[0].id != metric_id:
            raise ValueError(f"Quick metric with name '{name}' already exists")

        updates["name"] = name

    # Validate and update expression if provided
    if expression is not None and expression != data.get("expression"):
        # Parse expression (validates syntax)
        parsed = parse_expression(expression)

        # Validate base metrics exist in manifest
        manifest_metrics = storage.list_metrics(user.org_id)
        manifest_metric_names = {m.get("name") for m in manifest_metrics}
        missing = validate_metrics_exist(parsed.base_metrics, list(manifest_metric_names))
        if missing:
            raise ValueError(
                f"Expression references unknown metrics: {', '.join(missing)}"
            )

        updates["expression"] = expression
        updates["base_metrics"] = parsed.base_metrics

    # Update description if provided (empty string clears it)
    if description is not None:
        updates["description"] = description if description else None

    doc_ref.update(updates)

    # Return updated document
    updated_doc = doc_ref.get()
    result_data = _serialize_firestore_doc(updated_doc.to_dict())
    result_data["id"] = metric_id
    result_data["org_id"] = user.org_id

    return QuickMetric.model_validate(result_data)


async def delete_quick_metric(user: UserContext, metric_id: str) -> None:
    """Delete a quick metric.

    Args:
        user: Authenticated user context
        metric_id: Quick metric ID to delete

    Raises:
        ValueError: If metric not found
    """
    db = _get_firestore_client()
    doc_ref = db.collection("organizations").document(user.org_id).collection("quick_metrics").document(metric_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise ValueError(f"Quick metric with ID '{metric_id}' not found")

    doc_ref.delete()


# ============================================================================
# Tests
# ============================================================================

if __name__ == "__main__":
    print("Running quick_metrics tests...\n")
    tests_passed = 0
    tests_failed = 0

    def test(name: str, condition: bool, details: str = ""):
        global tests_passed, tests_failed
        if condition:
            print(f"  [PASS] {name}")
            tests_passed += 1
        else:
            print(f"  [FAIL] {name}: {details}")
            tests_failed += 1

    # Test 1: Basic parsing
    print("1. Basic parsing:")
    result = parse_expression("revenue / orders")
    test("Simple division", result.base_metrics == ["revenue", "orders"])
    test("Expression preserved", result.expression == "revenue / orders")

    # Test 2: Complex expression
    print("\n2. Complex expression:")
    result = parse_expression("(total_revenue - cogs) / total_revenue * 100")
    test("Extracts metrics", set(result.base_metrics) == {"total_revenue", "cogs"})
    test("No duplicates", len(result.base_metrics) == 2)

    # Test 3: Arithmetic operators
    print("\n3. All operators:")
    test("Addition", parse_expression("a + b").base_metrics == ["a", "b"])
    test("Subtraction", parse_expression("a - b").base_metrics == ["a", "b"])
    test("Multiplication", parse_expression("a * b").base_metrics == ["a", "b"])
    test("Division", parse_expression("a / b").base_metrics == ["a", "b"])

    # Test 4: Numbers in expressions
    print("\n4. Numbers:")
    result = parse_expression("revenue * 100")
    test("Metric with number", result.base_metrics == ["revenue"])
    result = parse_expression("0.5 * revenue + 0.5 * orders")
    test("Float constants", set(result.base_metrics) == {"revenue", "orders"})

    # Test 5: Unary operators
    print("\n5. Unary operators:")
    result = parse_expression("-revenue")
    test("Unary minus", result.base_metrics == ["revenue"])
    result = parse_expression("+revenue")
    test("Unary plus", result.base_metrics == ["revenue"])

    # Test 6: Evaluation
    print("\n6. Evaluation:")
    parsed = parse_expression("revenue / orders")
    val = evaluate_expression(parsed, {"revenue": 1000.0, "orders": 100.0})
    test("Simple division", val == 10.0)

    parsed = parse_expression("(total_revenue - cogs) / total_revenue * 100")
    val = evaluate_expression(parsed, {"total_revenue": 1000.0, "cogs": 400.0})
    test("Gross margin calc", val == 60.0, f"Expected 60.0, got {val}")

    parsed = parse_expression("-revenue + orders")
    val = evaluate_expression(parsed, {"revenue": 100.0, "orders": 150.0})
    test("Unary minus", val == 50.0, f"Expected 50.0, got {val}")

    # Test 7: Error cases
    print("\n7. Error handling:")

    try:
        parse_expression("")
        test("Empty expression", False, "Should raise error")
    except ExpressionError as e:
        test("Empty expression", "empty" in e.message.lower())

    try:
        parse_expression("revenue + ")
        test("Syntax error", False, "Should raise error")
    except ExpressionError as e:
        test("Syntax error", "syntax" in e.message.lower())

    try:
        parse_expression("import os")
        test("Import blocked", False, "Should raise error")
    except ExpressionError as e:
        # Import statement causes syntax error in eval mode (correct behavior)
        test("Import blocked", "syntax" in e.message.lower() or "disallowed" in e.message.lower())

    try:
        parse_expression("print(revenue)")
        test("Function call blocked", False, "Should raise error")
    except ExpressionError as e:
        test("Function call blocked", "disallowed" in e.message.lower())

    try:
        parse_expression("obj.attr")
        test("Attribute access blocked", False, "Should raise error")
    except ExpressionError as e:
        test("Attribute access blocked", "disallowed" in e.message.lower())

    try:
        parse_expression("100")  # No metrics
        test("No metrics error", False, "Should raise error")
    except ExpressionError as e:
        test("No metrics error", "at least one metric" in e.message.lower())

    # Test 8: Division by zero
    print("\n8. Division by zero:")
    parsed = parse_expression("revenue / orders")
    try:
        evaluate_expression(parsed, {"revenue": 1000.0, "orders": 0.0})
        test("Division by zero", False, "Should raise error")
    except ExpressionError as e:
        test("Division by zero", "division by zero" in e.message.lower())

    # Test 9: Missing metrics in evaluation
    print("\n9. Missing metrics:")
    parsed = parse_expression("revenue / orders")
    try:
        evaluate_expression(parsed, {"revenue": 1000.0})
        test("Missing metric", False, "Should raise error")
    except ExpressionError as e:
        test("Missing metric", "missing" in e.message.lower() and "orders" in e.message)

    # Test 10: Validate metrics exist
    print("\n10. Metric validation:")
    missing = validate_metrics_exist(["revenue", "orders"], ["revenue", "orders", "cogs"])
    test("All exist", missing == [])

    missing = validate_metrics_exist(["revenue", "unknown"], ["revenue", "orders"])
    test("Missing detected", missing == ["unknown"])

    missing = validate_metrics_exist(["a", "b"], [])
    test("All missing", set(missing) == {"a", "b"})

    # Test 11: Metric name validation
    print("\n11. Metric name validation:")
    result = parse_expression("metric_1 + metric_2")
    test("Underscores allowed", "metric_1" in result.base_metrics)

    result = parse_expression("_private + public")
    test("Leading underscore", "_private" in result.base_metrics)

    # Test 12: Whitespace handling
    print("\n12. Whitespace handling:")
    result = parse_expression("  revenue  /  orders  ")
    test("Extra whitespace", set(result.base_metrics) == {"revenue", "orders"})

    result = parse_expression("revenue/orders")
    test("No whitespace", set(result.base_metrics) == {"revenue", "orders"})

    # Test 13: Parentheses
    print("\n13. Parentheses:")
    # (a + b) * c vs a + b * c should both parse
    result1 = parse_expression("(a + b) * c")
    result2 = parse_expression("a + b * c")
    test("Grouped expression", set(result1.base_metrics) == {"a", "b", "c"})
    test("Ungrouped expression", set(result2.base_metrics) == {"a", "b", "c"})

    # Verify precedence is respected
    p1 = parse_expression("(a + b) * c")
    p2 = parse_expression("a + b * c")
    v1 = evaluate_expression(p1, {"a": 1, "b": 2, "c": 3})
    v2 = evaluate_expression(p2, {"a": 1, "b": 2, "c": 3})
    test("Parentheses affect order", v1 == 9 and v2 == 7, f"(1+2)*3={v1}, 1+2*3={v2}")

    # Summary
    print(f"\n{'='*50}")
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_failed}")
    print(f"{'='*50}")

    if tests_failed > 0:
        exit(1)
