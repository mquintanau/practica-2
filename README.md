# Práctica 2 resuelta: streams paralelos de Java

Los tres métodos solicitados están implementados en
`ejercicio_2/src/main/java/co/edu/unal/paralela/StudentAnalytics.java`.
Se conservaron las firmas, los métodos imperativos y las pruebas originales.
Los métodos paralelos no usan ciclos explícitos.

## Artefacto de estudio

- [Informe PDF](output/pdf/Practica_2_guia_de_estudio.pdf): marco teórico, código real explicado,
  ejemplo trabajado, complejidad, rendimiento, preguntas con respuestas y fuentes oficiales.
- [Versión editable Markdown](informe/guia_estudio.md).
- [Generador del informe](informe/generar_informe.py): requiere Python 3 y ReportLab;
  usa las fuentes Arial y Andale Mono de macOS. Ejecución: `python3 informe/generar_informe.py`.

## Verificación

Desde esta carpeta:

```bash
bash verificacion/verificar.sh
```

Requiere JDK 8 o posterior y Bash. Usa los JAR incluidos; no descarga dependencias.
Compila con API Java 8 (`--release 8` en JDK posteriores; `-source/-target 1.8` en JDK 8),
ejecuta JUnit y elimina las clases temporales. Devuelve un código de error si alguna prueba falla.
El registro más reciente se guarda en [resultados.txt](verificacion/resultados.txt).

La ejecución final documentada pasó **21 pruebas**: las 6 originales (3 de corrección y 3 de
rendimiento) y 15 adicionales. Entre las adicionales hay una comparación con 200 arreglos
pseudoaleatorios, además de fronteras de edad y nota, vacío, empates e integridad de la fuente.
Se ejecutó en OpenJDK 27/macOS aarch64, con 10 procesadores visibles y commonPool de paralelismo 9.
Se compiló para Java 8; no se ejecutó sobre una JVM 8.

Los umbrales de rendimiento dependen del entorno y pueden variar entre ejecuciones.
Se conservó un [registro inicial](verificacion/historial/01-collector-estandar.txt) donde
el collector estándar de nombres calculó correctamente, pero obtuvo speedup 4,612 frente
al mínimo 5,0. La implementación final usa una reducción por particiones con contadores
primitivos; la explicación está en el informe. No se cambiaron umbrales ni pruebas.

El intento `mvn -o test` encontró una restricción de acceso a un bloqueo de la caché `~/.m2`.
No se modificó el `pom.xml` de la guía; el script verifica directamente con `javac` y JUnit.

## Decisiones semánticas

- Promedio sin activos: `Double.NaN`, igual que el imperativo al calcular `0.0 / 0.0`.
- Sin inactivos: nombre `null`. Sin reprobados que cumplan el filtro: `0`.
- Reprobado: **inactivo** y edad **> 20** y nota **< 65**.
- Los nombres distinguen mayúsculas y minúsculas.
- En una moda empatada no hay una regla de desempate en la guía: se acepta cualquier nombre
  con frecuencia máxima. El `HashMap` original no define el orden; ambas versiones pueden
  elegir diferentes ganadores. Con moda única se verifica la coincidencia exacta.
- Se trabaja con arreglos y estudiantes no nulos, nombres no nulos y edades finitas.
  No se añadió validación de entradas fuera de ese dominio.

Las modificaciones de código del ejercicio se limitaron a `StudentAnalytics.java`.
Las pruebas adicionales, documentación e informe están fuera de sus fuentes originales.
