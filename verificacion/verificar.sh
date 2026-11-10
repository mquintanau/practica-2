#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$(mktemp -d "$ROOT/verificacion/.build.XXXXXX")"
trap 'rm -rf -- "$BUILD"' EXIT
JARS="$ROOT/ejercicio_2/junit-4.12.jar:$ROOT/ejercicio_2/hamcrest-core-1.3.jar"
COMPILER_VERSION="$(javac -version 2>&1)"
if [[ "$COMPILER_VERSION" == "javac 1.8."* ]]; then
    COMPILER_OPTIONS=(-source 1.8 -target 1.8)
else
    COMPILER_OPTIONS=(--release 8 -Xlint:-options)
fi
{
    javac "${COMPILER_OPTIONS[@]}" -encoding UTF-8 -cp "$JARS" -d "$BUILD" \
        "$ROOT"/ejercicio_2/src/main/java/co/edu/unal/paralela/*.java \
        "$ROOT/ejercicio_2/src/test/java/co/edu/unal/paralela/StudentAnalyticsTest.java" \
        "$ROOT/verificacion/RunTests.java"
    # Suite adicional desactivada: StudentAnalyticsEdgeTest.java no se compila.
    java -Xmx4g -cp "$BUILD:$JARS" RunTests
} 2>&1 | tee "$ROOT/verificacion/resultados.txt"
