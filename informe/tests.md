# Cómo se componen y aprueban los tests

La práctica tiene **21 tests** organizados en dos suites: **6 originales** y **15 adicionales**.
Una suite es una clase que agrupa métodos de prueba. Un test puede contener varias aserciones
y recorrer muchos conjuntos de datos: los 200 arreglos de la comparación aleatoria pertenecen
a **un solo test**, no a 200 tests independientes.

## 1. Archivos y recorrido de ejecución

| Archivo | Responsabilidad |
| --- | --- |
| [`StudentAnalyticsTest.java`](../ejercicio_2/src/test/java/co/edu/unal/paralela/StudentAnalyticsTest.java) | Pruebas originales de corrección y rendimiento, sin modificaciones. |
| [`StudentAnalyticsEdgeTest.java`](../verificacion/StudentAnalyticsEdgeTest.java) | Casos pequeños, fronteras, empates y comparación aleatoria. |
| [`RunTests.java`](../verificacion/RunTests.java) | Ejecuta las dos suites mediante JUnitCore y reúne los resultados. |
| [`verificar.sh`](../verificacion/verificar.sh) | Compila, ejecuta el runner, guarda la salida y elimina las clases temporales. |
| [`resultados.txt`](../verificacion/resultados.txt) | Evidencia de una ejecución: entorno, cantidad de pruebas, fallos y resultado global. |

El recorrido es:

```text
verificar.sh
  -> javac: compilar aplicación, pruebas y runner
  -> java: ejecutar RunTests
       -> JUnitCore: StudentAnalyticsTest       (6 tests)
       -> JUnitCore: StudentAnalyticsEdgeTest   (15 tests)
  -> tee: mostrar y guardar el resultado
```

Las clases de prueba heredan de `junit.framework.TestCase`. Usan el estilo de JUnit 3:
métodos públicos `void`, sin parámetros y con un nombre que empieza por `test`.
El runner de JUnit 4.12 incluido es compatible con ese estilo; por eso no hace falta `@Test`.
Los métodos auxiliares como `generateStudentData`, `student` y los terminados en `Helper`
preparan o ejecutan trabajo para los tests, pero no se cuentan como pruebas independientes.
El orden de ejecución no debe asumirse a partir de su posición en el archivo.

## 2. Anatomía de un test y significado de las aserciones

Cada prueba sigue tres pasos: **preparar datos**, **invocar el método** y **comprobar el resultado**.
Por ejemplo, en la frontera de nota se crean tres estudiantes inactivos mayores de 20 años,
con notas 64, 65 y 66. Se ejecuta el conteo paralelo y se exige que devuelva 1:

```java
Student[] data = {
    student("Ana", 21, 64, false),
    student("Luis", 21, 65, false),
    student("Eva", 21, 66, false)
};
assertEquals(1,
    analytics.countNumberOfFailedStudentsOlderThan20ParallelStream(data));
```

Este caso detectaría el error de usar `<= 65` en lugar de `< 65`: devolvería 2 y fallaría.

| Aserción usada | Cuándo se cumple |
| --- | --- |
| `assertEquals(esperado, obtenido)` | Los enteros o los contenidos de los nombres coinciden. |
| `assertEquals(esperado, obtenido, delta)` | Los valores `double` están dentro de la tolerancia indicada. |
| `assertTrue(condicion)` | La condición es verdadera; por ejemplo, que un speedup supere su umbral. |
| `assertNull(valor)` | El resultado es `null`, como la moda cuando no hay inactivos. |
| `assertSame(antes, despues)` | Se conserva la misma referencia de objeto, no solo un contenido equivalente. |
| `assertTrue(Double.isNaN(valor))` | El promedio sin activos conserva el resultado indefinido `NaN`. |

**Un test aprueba cuando llega a su final sin aserciones fallidas ni excepciones no controladas.**
Si una aserción falla, esa invocación termina: las aserciones posteriores de ese test no se ejecutan.
Una excepción como `UnsupportedOperationException` o `NullPointerException` también hace fallar la prueba.
JUnit recoge el problema y continúa con los demás tests de la suite.

## 3. Cómo se componen las 6 pruebas originales

### Datos comunes

Cada invocación de un helper genera un arreglo nuevo con:

- **2.000.000 estudiantes**.
- **600.000 activos**, ubicados al principio del arreglo; los **1.400.000 restantes son inactivos**.
- Nombres y apellidos elegidos entre seis alternativas cada uno.
- Edades `double` en el intervalo **[0, 100)** y notas enteras entre **1 y 100**, inclusive.
- Generador `Random(123)`: la semilla permite repetir los mismos datos.

La versión **imperativa** de cada consulta sirve como referencia u oráculo.
El helper calcula primero ese valor esperado y luego comprueba la versión paralela.

| Test original | Condición de aprobación |
| --- | --- |
| `testAverageAgeOfEnrolledStudents` | Error absoluto del promedio paralelo frente al imperativo **< 1E-5**. |
| `testMostCommonFirstNameOfInactiveStudents` | El nombre devuelto coincide exactamente con el imperativo para los datos generados. |
| `testCountNumberOfFailedStudentsOlderThan20` | El conteo paralelo coincide exactamente con el imperativo. |
| `testAverageAgeOfEnrolledStudentsPerf` | Cumple la comparación del promedio **y** obtiene **S > 1,2**. |
| `testMostCommonFirstNameOfInactiveStudentsPerf` | Cumple la comparación del nombre **y** obtiene **S >= 0,5 × p**. |
| `testCountNumberOfFailedStudentsOlderThan20Perf` | Cumple la comparación del conteo **y** obtiene **S > 1,2**. |

`p` es el valor de `Runtime.getRuntime().availableProcessors()`: procesadores visibles para la JVM,
que no necesariamente representan núcleos físicos. En el registro publicado, `p = 10`;
por tanto, el umbral de la moda es `0,5 × 10 = 5`.

### Cómo se calcula el rendimiento

Los tres helpers siguen esta secuencia:

1. Generar los datos y obtener el resultado imperativo de referencia.
2. Medir un bloque de invocaciones imperativas con `System.currentTimeMillis()`.
3. Ejecutar una vez la versión paralela y comprobar su resultado contra la referencia.
4. Medir un bloque de invocaciones paralelas con el mismo número de repeticiones.
5. Devolver el cociente **S = tiempo secuencial / tiempo paralelo**.

Los tests de corrección llaman al helper con **1 repetición** por bloque medido y no ponen
un umbral al cociente devuelto. Los tests terminados en `Perf` usan **10 repeticiones**
y sí comprueban el umbral. La generación de datos queda fuera de los bloques cronometrados.
Los tiempos corresponden a bloques completos, no a una sola llamada; al usar el mismo
número de repeticiones, el cociente compara el mismo volumen de invocaciones.

Ejemplos **ilustrativos**, no mediciones nuevas:

| Secuencial | Paralelo | S | Interpretación |
| --- | --- | --- | --- |
| 120 ms | 100 ms | 1,2 | No aprueba promedio/conteo: se exige **mayor**, no igual. |
| 121 ms | 100 ms | 1,21 | Aprueba el umbral de promedio/conteo si el resultado también es correcto. |
| 500 ms | 100 ms | 5 | Aprueba el umbral de moda con `p = 10`, porque aquí sí se acepta igualdad. |
| 480 ms | 100 ms | 4,8 | No aprueba el umbral de moda con `p = 10`, aunque el nombre sea correcto. |

## 4. Cómo se componen las 15 pruebas adicionales

Estas pruebas usan resultados calculables a mano y condiciones de frontera.
No exigen tiempos mínimos ni modifican los tests de la guía.

| Test adicional | Datos o situación | Qué exige para aprobar |
| --- | --- | --- |
| `testEmptyArray` | Arreglo sin estudiantes. | Promedio `NaN`, nombre `null`, conteo `0`. |
| `testAllActive` | Activos de 18 y 24 años. | Promedio `21`, nombre `null`, conteo `0`. |
| `testAllInactive` | Dos Ana de 22 y 24 años, notas 64 y 50. | Promedio `NaN`, moda `Ana`, conteo `2`. |
| `testFractionalAgesAndActiveFilter` | Activos de 18,5 y 21,25; inactivo de 90. | Promedio `19,875` con tolerancia `1E-12`; excluye al inactivo. |
| `testStrictAgeBoundary` | Inactivos de 19,99; 20; 20,0001 años, nota 64. | Conteo `1`: solo la edad estrictamente mayor que 20. |
| `testStrictGradeBoundary` | Inactivos de 21 años, notas 64, 65 y 66. | Conteo `1`: solo la nota estrictamente menor que 65. |
| `testActiveStudentWithLowGradeIsExcluded` | Dos estudiantes de 25 años y nota 10, uno activo. | Conteo `1`: el activo no se incluye. |
| `testModeUsesOnlyInactiveStudents` | Tres Ana activos; dos Eva y un Luis inactivos. | Moda `Eva`, aunque Ana aparezca más en todo el arreglo. |
| `testNamesAreCaseSensitive` | Un `Ana` y dos `ana`, todos inactivos. | Moda `ana`: no une nombres por diferencias de mayúsculas. |
| `testTiedModeAndHashCollision` | `FB` y `Ea` aparecen dos veces; `Otro`, una. | Acepta `FB` o `Ea`. Sus hashes coinciden, pero son claves distintas. |
| `testSourceArrayIsUnchanged` | Copia superficial del arreglo antes de las tres consultas. | `assertSame` en cada posición confirma las referencias originales y su orden. |
| `testSingleActiveStudent` | Una Ana activa de 20,5 años y nota 64. | Promedio `20,5`, nombre `null`, conteo `0`. |
| `testSingleInactiveStudent` | Una Ana inactiva de 20,5 años y nota 64. | Promedio `NaN`, moda `Ana`, conteo `1`. |
| `testRepeatedCallsDoNotShareState` | Alterna dos arreglos 12 veces usando el mismo objeto de análisis. | Moda `Ana`/`null` y conteo `1`/`0`, sin arrastrar acumulaciones. |
| `testRandomizedEquivalence` | 200 arreglos con `Random(20261109L)`. | Comprueba promedio, conteo y validez de la moda en cada arreglo. |

### Qué comprueba exactamente la prueba aleatoria

Cada arreglo tiene una longitud entre **0 y 3000**, inclusive. Se elige entre siete nombres,
se generan edades en **[0, 100)**, notas enteras entre **0 y 100**, inclusive,
y un estado activo/inactivo pseudoaleatorio. Esos rangos difieren deliberadamente de los originales.

Para cada arreglo se comprueban tres propiedades:

1. **Promedio:** coincide con el imperativo dentro de una tolerancia de `1E-9`.
   Si la referencia es `NaN`, exige también `NaN` en el paralelo.
2. **Conteo:** igualdad exacta con el imperativo.
3. **Moda:** un mapa construido por un recorrido secuencial independiente cuenta solo inactivos.
   Si está vacío, el resultado debe ser `null`. Si tiene entradas, el nombre devuelto
   debe existir y alcanzar la frecuencia máxima. Si hay una única moda,
   también debe coincidir exactamente con la versión imperativa.

En un empate no se impone un ganador alfabético: el `HashMap` del imperativo no define un orden.
La prueba original compara nombres exactamente para su conjunto fijo; la adicional con empates
comprueba la propiedad matemática de tener frecuencia máxima.

## 5. Cómo se decide la aprobación global

Desde la raíz del repositorio:

```bash
bash verificacion/verificar.sh
```

El script requiere un JDK 8 o posterior. Usa los JAR locales de JUnit y Hamcrest y no descarga
dependencias. Crea una carpeta temporal, compila las clases y ejecuta `RunTests` con `-Xmx4g`.
La opción configura un máximo de heap; no significa que siempre se consuman 4 GB.

`RunTests` ejecuta cada suite y consulta su cantidad de pruebas, fallos e ignoradas.
Acumula `getFailureCount()` de ambas suites:

- Si el total de fallos es **0**, imprime `RESULTADO: OK` y termina normalmente, con código **0**.
- Si hay **uno o más fallos**, imprime sus trazas, muestra `RESULTADO: FALLO`
  y termina con código **1**.
- Un error al compilar o iniciar las clases también impide completar correctamente el comando.
  `set -euo pipefail` evita que la escritura mediante `tee` oculte un fallo de la ejecución.
- El bloque de salida se muestra en pantalla y se guarda en `verificacion/resultados.txt`.
  La carpeta de clases temporales se elimina al salir.

Para comprobar que se ejecutó **toda la cobertura prevista**, hay que leer los dos resúmenes:

```text
StudentAnalyticsTest: 6 pruebas, 0 fallos, 0 ignoradas
StudentAnalyticsEdgeTest: 15 pruebas, 0 fallos, 0 ignoradas
RESULTADO: OK
```

Ese fragmento es un resumen del formato; el archivo real incluye paquetes, entorno y tiempos.
El runner decide `OK` por el número de fallos: **no tiene una aserción adicional que exija
exactamente 21 pruebas o cero ignoradas**. Por eso conviene revisar también los contadores.

## 6. Qué significa el resultado publicado y cómo leer un fallo

El [registro publicado](../verificacion/resultados.txt) del **9 de noviembre de 2026** muestra
6 originales y 15 adicionales, sin fallos ni ignoradas, sobre OpenJDK 27/macOS aarch64.
Los **819 ms** y **61 ms** son duraciones de suites completas: no son los tiempos de
una consulta individual ni permiten reconstruir sus speedups.

| Señal en la salida | Cómo interpretarla |
| --- | --- |
| `Expected ... but found ...`, `Mismatch in calculated values` o un `assertEquals` fallido | Revisar filtros, cálculo y valor devuelto. Es un problema de corrección para ese caso. |
| `err = ...` en el promedio original | La diferencia numérica no fue menor que `1E-5`. Revisar qué edades se promedian y la precisión. |
| `Expected speedup ... but was ...` | La comprobación de resultado del helper ya pasó, pero el cociente temporal no alcanzó el umbral. |
| Traza con una excepción | Localizar la primera línea relevante de la aplicación o del test y revisar la causa. |
| Mensaje de `javac` o imposibilidad de iniciar Java | La suite no completó su ejecución; primero hay que resolver la compilación o el entorno. |

Se conserva un [fallo histórico de rendimiento](../verificacion/historial/01-collector-estandar.txt):
la implementación inicial de moda obtuvo **S = 4,612...**, inferior a **5**.
El nombre calculado había aprobado su comparación. Después se cambió la reducción y se
documentó la ejecución con las 21 pruebas aprobadas.

Los tests de rendimiento usan reloj de milisegundos y no controlan completamente JIT,
recolección de basura, carga del sistema o acceso a memoria. Tampoco protegen explícitamente
el cociente frente a un intervalo paralelo medido como cero. Por eso un resultado temporal
puede variar y estos tests no sustituyen un benchmark con mediciones más robustas.
No se deben cambiar los umbrales ni repetir hasta obtener un resultado favorable ocultando los demás.

Aprobar las pruebas demuestra que se cumplieron **los casos y umbrales ejecutados en ese entorno**.
No demuestra por sí solo corrección para toda entrada posible, una aceleración universal,
ausencia formal de carreras de datos ni el uso de streams paralelos sin ciclos:
estos últimos aspectos también se revisan en la implementación.
Las pruebas se limitan a estudiantes y nombres no nulos con edades finitas;
no cubren entradas `null`, edades infinitas o `NaN` en los datos.
