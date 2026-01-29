from collections.abc import Collection

ADD_OPENS: Collection[str] = [
    # Arrow reflexive access: https://github.com/activeviam/activepivot/pull/4297/files#diff-d9ef6fa90dda49aa1ec2907eba7be19c916c5f553c9846b365d30a307740aea2
    "--add-opens=java.base/java.nio=ALL-UNNAMED",
    # Py4J reflexive access: java.lang.reflect.InaccessibleObjectException: Unable to make public java.lang.Object[] java.util.HashMap$KeySet.toArray() accessible: module java.base does not "opens java.util" to unnamed module @647fd8ce
    "--add-opens=java.base/java.util=ALL-UNNAMED",
    "--add-opens=java.base/java.lang=ALL-UNNAMED",
]
