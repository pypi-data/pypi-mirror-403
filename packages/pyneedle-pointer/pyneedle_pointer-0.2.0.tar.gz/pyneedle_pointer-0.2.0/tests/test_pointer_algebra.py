from needle.pointer import L, SemanticPointer, PointerSet


# --- SemanticPointer (L) Tests ---


def test_pointer_core_behavior():
    # Root
    assert str(L) == ""
    assert repr(L) == "<L: (root)>"

    # Attribute access
    p = L.auth.login.success
    assert isinstance(p, SemanticPointer)
    assert str(p) == "auth.login.success"
    assert repr(p) == "<L: 'auth.login.success'>"

    # Equality
    assert p == "auth.login.success"
    assert p == SemanticPointer("auth.login.success")
    assert p != L.auth.login.failure


def test_pointer_hashable():
    d = {L.user.name: "Alice", L.user.id: 123}
    assert d[L.user.name] == "Alice"
    assert d[SemanticPointer("user.id")] == 123


def test_pointer_dynamic_composition_operators():
    base = L.payment
    method = "credit_card"
    status_code = 200

    # Using +
    p1 = base + method + "success"
    assert p1 == "payment.credit_card.success"

    # Using /
    p2 = base / method / "error" / str(status_code)
    assert p2 == "payment.credit_card.error.200"

    # Mixing operators
    p3 = L / "user" + "profile"
    assert p3 == "user.profile"


def test_pointer_multiplication_distributes_to_set():
    base = L.api.v1
    endpoints = {"users", "products"}

    result = base * endpoints
    assert isinstance(result, PointerSet)
    assert len(result) == 2
    assert L.api.v1.users in result
    assert L.api.v1.products in result

    # NEW: Test that division by set behaves exactly like multiplication
    result_div = base / endpoints
    assert result_div == result


def test_pointer_atomic_vs_container_behavior():
    # 1. Atomic Input -> Atomic Output (Pointer)
    # Even with '*', if input is atomic string, it acts as composition
    p1 = L.api * "v1"
    assert isinstance(p1, SemanticPointer)
    assert p1 == "api.v1"

    # Division behaves the same
    p2 = L.api / "v1"
    assert p2 == p1

    # 2. Container Input -> Collection Output (PointerSet)
    # Even if list has only 1 item
    ps1 = L.api * ["v1"]
    assert isinstance(ps1, PointerSet)
    assert L.api.v1 in ps1

    # Division behaves the same
    ps2 = L.api / ["v1"]
    assert ps2 == ps1


def test_pointer_recursive_flattening():
    # Test L[[[1, 2]]] -> {L.1, L.2}

    # Using getitem
    ps1 = L[[[1, 2]]]
    assert isinstance(ps1, PointerSet)
    assert ps1 == {L["1"], L["2"]}

    # Using multiplication
    ps2 = L * [[[1], 2]]
    assert ps2 == ps1

    # Using division
    ps3 = L / (1, (2,))
    assert ps3 == ps1


# --- PointerSet (Ls) Tests ---


def test_pointer_set_behaves_like_a_set():
    s1 = PointerSet([L.a, L.b])
    s2 = PointerSet([L.b, L.c])

    assert len(s1) == 2
    assert L.a in s1
    assert L.c not in s1

    # Union
    union = s1 | s2
    assert union == {L.a, L.b, L.c}


def test_pointer_set_broadcasting_operators():
    base_set = L * {"user", "admin"}  # {L.user, L.admin}
    suffix = "profile"

    # Using /
    result_div = base_set / suffix
    assert isinstance(result_div, PointerSet)
    assert result_div == {L.user.profile, L.admin.profile}

    # Using +
    result_add = base_set + "dashboard"
    assert result_add == {L.user.dashboard, L.admin.dashboard}


def test_pointer_set_multiplication_cartesian_product():
    roles = L * {"admin", "guest"}
    actions = {"read", "write"}

    permissions = roles * actions

    expected = {L.admin.read, L.admin.write, L.guest.read, L.guest.write}
    assert permissions == expected


def test_pointer_getitem_for_non_identifiers():
    p = L.errors[404]
    assert p == "errors.404"

    p2 = L.config["user-settings"]
    assert p2 == "config.user-settings"

    p3 = L.a[1]["b"]
    assert p3 == "a.1.b"


def test_pointer_set_chained_broadcasting():
    # This test now passes because __getitem__ is implemented.
    result = (L * {"http", "ftp"}) / "errors" * {"404", "500"}

    expected = {
        L.http.errors["404"],
        L.http.errors["500"],
        L.ftp.errors["404"],
        L.ftp.errors["500"],
    }

    assert result == expected


def test_pointer_multiplication_is_flexible_and_chainable():
    # 1. Chaining with strings and sets
    result1 = L.api * {"v1", "v2"} * "users"
    expected1 = {L.api.v1.users, L.api.v2.users}
    assert result1 == expected1

    # 2. Chaining with another pointer
    base_set = L * {"admin", "guest"}
    suffix = L.permissions
    result2 = base_set * suffix
    expected2 = {L.admin.permissions, L.guest.permissions}
    assert result2 == expected2

    # 3. Chaining a set multiplication with a pointer resolves the bug
    result3 = L.api * {"users", "products"} * L.errors
    expected3 = {L.api.users.errors, L.api.products.errors}
    assert result3 == expected3

    # 4. Using non-string, non-pointer objects (fallback to str)
    result4 = L.status * 200
    expected4 = L.status["200"]
    assert result4 == expected4

    # 5. PointerSet with non-string, non-pointer objects
    result5 = (L * {"http", "ftp"}) * 404
    expected5 = {L.http["404"], L.ftp["404"]}
    assert result5 == expected5


def test_pointer_getitem_multi_index():
    # Multi-index L['a', 'b'] should return a PointerSet
    ps = L["a", "b"]
    assert isinstance(ps, PointerSet)
    assert len(ps) == 2
    assert L.a in ps
    assert L.b in ps

    # Chaining with multi-index: L.api['v1', 'v2'].users
    # This proves broadcasting works after the shortcut creation.
    ps2 = L.api["v1", "v2"].users
    assert ps2 == {L.api.v1.users, L.api.v2.users}


def test_pointer_wildcard_indexing():
    # Single index L['+'] should return a single SemanticPointer (Pattern)
    p1 = L["+"]
    assert isinstance(p1, SemanticPointer)
    assert str(p1) == "+"

    # MQTT style wildcard construction
    p2 = L.check["#"]
    assert isinstance(p2, SemanticPointer)
    assert str(p2) == "check.#"

    # Chaining after wildcard
    p3 = L.check["+"] / "error"
    assert str(p3) == "check.+.error"


def test_pointer_set_getitem_broadcasting():
    # Test broadcasting of __getitem__ on a PointerSet
    ps = L["auth", "api"][0]
    assert ps == {L.auth[0], L.api[0]}

    # Combined complex chaining
    ps2 = L["http", "ftp"].v1[404].detail
    assert ps2 == {L.http.v1[404].detail, L.ftp.v1[404].detail}


def test_pointer_set_complex_nested_multi_index():
    # Fix for: L['a','b'][0][1,2] -> TypeError: unhashable type: 'PointerSet'
    result = L["a", "b"][0][1, 2]

    expected = {
        L.a[0][1],
        L.a[0][2],
        L.b[0][1],
        L.b[0][2],
    }
    assert result == expected
    assert isinstance(result, PointerSet)
