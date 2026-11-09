"""Genera el PDF de estudio y su versión Markdown a partir del código real.

Requiere Python 3 y reportlab. Ejecutar desde cualquier carpeta.
"""
from pathlib import Path
import html
import re
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Preformatted, PageBreak, KeepTogether, Flowable,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'output' / 'pdf'
OUTPUT.mkdir(parents=True, exist_ok=True)
SOURCE = ROOT / 'ejercicio_2/src/main/java/co/edu/unal/paralela/StudentAnalytics.java'
CODE = SOURCE.read_text(encoding='utf-8')
FONTS = Path('/System/Library/Fonts/Supplemental')
for name, file in [('Body', 'Arial.ttf'), ('Strong', 'Arial Bold.ttf'),
                   ('Mono', 'Andale Mono.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONTS / file)))

NAVY = colors.HexColor('#163249')
TEAL = colors.HexColor('#007E83')
INK = colors.HexColor('#203547')
MUTED = colors.HexColor('#526577')
PALE = colors.HexColor('#EDF5F6')
LINE = colors.HexColor('#D9E3E8')
W = 481.28
STYLES = {
    'kicker': ParagraphStyle('kicker', fontName='Strong', fontSize=9, leading=12,
                              textColor=TEAL, spaceAfter=9),
    'title': ParagraphStyle('title', fontName='Strong', fontSize=26, leading=30,
                             textColor=NAVY, spaceAfter=13),
    'intro': ParagraphStyle('intro', fontName='Body', fontSize=11.5, leading=16,
                             textColor=MUTED, spaceAfter=16),
    'h2': ParagraphStyle('h2', fontName='Strong', fontSize=12, leading=15,
                          textColor=NAVY, spaceBefore=12, spaceAfter=6,
                          keepWithNext=True),
    'body': ParagraphStyle('body', fontName='Body', fontSize=10.2, leading=14.5,
                            textColor=INK, spaceAfter=8),
    'small': ParagraphStyle('small', fontName='Body', fontSize=9.1, leading=12.6,
                             textColor=MUTED, spaceAfter=7),
    'cell': ParagraphStyle('cell', fontName='Body', fontSize=9.3, leading=12.8,
                            textColor=INK),
    'headcell': ParagraphStyle('headcell', fontName='Strong', fontSize=9.2,
                                leading=12.5, textColor=colors.white),
    'code': ParagraphStyle('code', fontName='Mono', fontSize=8.3, leading=11.5,
                            textColor=INK, backColor=PALE, borderPadding=9,
                            spaceBefore=5, spaceAfter=12),
}
story = []
markdown = ['# Práctica 2 - Streams paralelos de Java\n',
            'Universidad Nacional de Colombia | Computación Paralela y Distribuida\n',
            'Solución explicada y guía de sustentación. Preparado el 9 de noviembre de 2026.\n']
page_count = 0


def rich(text):
    text = html.escape(text)
    text = re.sub(r'`([^`]+)`', r'<font name="Mono">\1</font>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<font name="Strong">\1</font>', text)
    return text


def page(label, title, intro=''):
    global page_count
    if page_count:
        story.append(PageBreak())
    page_count += 1
    story.append(Paragraph(label.upper(), STYLES['kicker']))
    story.append(Paragraph(rich(title), STYLES['title']))
    markdown.append('\n## ' + title + '\n')
    if intro:
        story.append(Paragraph(rich(intro), STYLES['intro']))
        markdown.append(intro + '\n')


def para(text, small=False):
    story.append(Paragraph(rich(text), STYLES['small' if small else 'body']))
    markdown.append(text + '\n')


def heading(text):
    story.append(Paragraph(rich(text), STYLES['h2']))
    markdown.append('\n### ' + text + '\n')


def bullet(text):
    p = Paragraph(rich(text), STYLES['body'])
    t = Table([[Paragraph('•', STYLES['body']), p]], colWidths=[13, W - 13])
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                           ('LEFTPADDING', (0, 0), (-1, -1), 0),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                           ('TOPPADDING', (0, 0), (-1, -1), 0),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
    story.append(t)
    markdown.append('- ' + text + '\n')


def table(headers, rows, widths):
    data = [[Paragraph(rich(v), STYLES['headcell']) for v in headers]]
    data += [[Paragraph(rich(str(v)), STYLES['cell']) for v in row] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 1), (-1, -1), 0.4, LINE),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.extend([t, Spacer(1, 10)])
    markdown.append('| ' + ' | '.join(headers) + ' |\n')
    markdown.append('| ' + ' | '.join(['---'] * len(headers)) + ' |\n')
    markdown.extend('| ' + ' | '.join(map(str, row)) + ' |\n' for row in rows)


def code(text):
    for line in text.splitlines():
        if pdfmetrics.stringWidth(line, 'Mono', 8.3) > W - 18:
            raise ValueError('Línea de código demasiado larga: ' + line)
    story.append(Preformatted(text, STYLES['code']))
    markdown.append('\n```java\n' + text + '\n```\n')


def method(name):
    start = CODE.index('    public ', CODE.index('public final class'))
    match = re.search(r'    public \w+ ' + re.escape(name) + r'\(', CODE)
    if not match:
        raise ValueError(name)
    start = match.start()
    brace = CODE.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (CODE[end] == '{') - (CODE[end] == '}')
        end += 1
    return '\n'.join(line[4:] if line.startswith('    ') else line
                     for line in CODE[start:end].splitlines())


class PartitionDiagram(Flowable):
    def __init__(self):
        super().__init__()
        self.width = W
        self.height = 140

    def draw(self):
        c = self.canv
        c.setFillColor(NAVY)
        c.setFont('Strong', 10)
        c.drawCentredString(W / 2, 127, 'Student[]: una fuente, varias particiones')
        c.setStrokeColor(LINE)
        c.line(W / 2, 117, W / 2, 103)
        c.line(74, 103, W - 74, 103)
        for x, label, values in [(0, 'Partición A', 'filtrar + acumular'),
                                 (166, 'Partición B', 'filtrar + acumular'),
                                 (332, 'Partición C', 'filtrar + acumular')]:
            center = x + 74
            c.line(center, 103, center, 88)
            c.setFillColor(PALE)
            c.roundRect(x, 42, 149, 46, 6, stroke=0, fill=1)
            c.setFillColor(NAVY)
            c.setFont('Strong', 9.5)
            c.drawCentredString(center, 70, label)
            c.setFont('Body', 9)
            c.drawCentredString(center, 55, values)
            c.line(center, 42, center, 31)
        c.line(74, 31, W - 74, 31)
        c.line(W / 2, 31, W / 2, 20)
        c.setFillColor(TEAL)
        c.setFont('Strong', 10)
        c.drawCentredString(W / 2, 5, 'Combinar resultados parciales -> resultado final')


page('01 / Propósito y alcance', 'Práctica 2\nStreams paralelos',
     'Solución implementada, marco teórico y preparación para la sustentación.')
para('Universidad Nacional de Colombia. Computación Paralela y Distribuida. '
     'Ejercicio 2. Fecha de preparación: 9 de noviembre de 2026.')
heading('Qué quedó resuelto')
table(['Consulta', 'Selección', 'Resultado'], [
    ['Promedio de edad', 'Estudiantes activos', 'double; NaN si no hay activos'],
    ['Nombre más frecuente', 'Estudiantes inactivos', 'String; null si no hay inactivos'],
    ['Cantidad de reprobados', 'Inactivos, edad > 20 y nota < 65', 'int; 0 si nadie cumple'],
], [132, 191, W - 323])
para('La implementación conserva las seis firmas públicas, mantiene los tres métodos '
     'imperativos y usa streams paralelos en las tres consultas solicitadas. No introduce '
     'ciclos for, while o do en sus cuerpos.')
heading('Cómo recorrer este informe')
bullet('Páginas 2 a 6: conceptos, implementación real y justificación de las operaciones.')
bullet('Página 7: un conjunto de estudiantes resuelto a mano, de principio a fin.')
bullet('Páginas 8 y 9: complejidad, rendimiento y evidencia de verificación.')
bullet('Páginas 10 a 12: preguntas con respuestas, ejercicios y fuentes primarias.')
heading('Archivos que debes reconocer')
para('`ejercicio_2/src/main/java/co/edu/unal/paralela/StudentAnalytics.java` contiene la '
     'solución. `verificacion/` contiene pruebas adicionales y el registro de ejecución. '
     'La guía original y las pruebas proporcionadas se conservaron.', small=True)
para('Alcance de los datos: arreglos y estudiantes no nulos, nombres no nulos y edades '
     'finitas del dominio académico. No se añadió una capa de validación de datos.', small=True)

page('02 / Marco teórico', 'Del ciclo al pipeline',
     'Un stream describe qué calcular sobre una secuencia de datos.')
para('Una colección o un arreglo almacena datos. Un stream organiza su recorrido. '
     'Puede consumir la misma fuente sin modificarla, pero cada stream se utiliza una sola vez. [1, 2]')
table(['Elemento', 'Papel en esta práctica'], [
    ['Fuente', '`Stream.of(studentArray)` produce un Stream<Student>.'],
    ['Modo de ejecución', '`.parallel()` habilita la ejecución paralela del pipeline.'],
    ['Operación intermedia', '`filter` conserva elementos; `mapToDouble` extrae edades.'],
    ['Operación terminal', '`average`, `collect`, `max` o `count` produce un resultado.'],
    ['Evaluación diferida', 'La selección y transformación se recorren al iniciar la terminal.'],
], [134, W - 134])
story.append(PartitionDiagram())
markdown.append('Dividir Student[] -> filtrar y acumular por partición -> combinar resultados.\n')
heading('Qué significa ejecutar en paralelo')
para('El arreglo permite dividir rangos de índices con bajo costo. En OpenJDK, los streams '
     'paralelos se ejecutan habitualmente mediante Fork/Join: tareas procesan particiones y '
     'se combinan sus resultados. No se crea un hilo por estudiante ni se promete un número '
     'fijo de hilos. El hilo que invoca también puede participar. [7, 8]')
para('Paralelismo significa que parte del trabajo puede ocurrir simultáneamente; '
     'concurrencia significa que varias tareas progresan durante el mismo intervalo. '
     'Aquí se aplica paralelismo de datos: la consulta se repite sobre diferentes subconjuntos.')
heading('Condiciones para una reducción correcta')
para('Las funciones deben evitar interferir con la fuente y depender de estado compartido '
     'cambiante. Las reducciones deben tener una combinación compatible con su acumulación '
     'y con una identidad. La suma de conteos satisface estas condiciones. [2, 3]')

page('03 / Implementación 1', 'Promedio de edad de activos',
     'Filtrar estudiantes, extraer edades y reducir a una media.')
code(method('averageAgeOfEnrolledStudentsParallelStream'))
heading('Por qué cada operación está ahí')
bullet('`filter(Student::checkIsCurrent)` conserva únicamente los activos. La referencia '
       'a método equivale a la lambda `s -> s.checkIsCurrent()`.')
bullet('`mapToDouble(Student::getAge)` conserva edades fraccionarias y produce un '
       'DoubleStream, evitando envolver cada edad en un objeto Double.')
bullet('`average()` entrega un OptionalDouble. `orElse(Double.NaN)` conserva el caso '
       'vacío de la versión imperativa: la división 0.0 / 0.0 produce NaN. [4]')
heading('El promedio no se combina promediando promedios')
para('Sean A los estudiantes activos. La consulta calcula suma(edad de s en A) / |A|. '
     'Un resultado parcial útil es el par (suma, cantidad), cuya combinación es '
     '(S1 + S2, C1 + C2). Solo al final se divide la suma entre la cantidad total.')
table(['Partición', 'Suma', 'Cantidad', 'Promedio local'], [
    ['A: edades 18 y 22', '40', '2', '20'],
    ['B: edad 24', '24', '1', '24'],
    ['Combinación correcta', '64', '3', '21,333333...'],
], [183, 74, 80, W - 337])
para('Promediar 20 y 24 daría 22: es incorrecto porque ambas particiones tienen diferente '
     'cantidad de estudiantes. `average()` gestiona la acumulación y combinación por nosotros.')
heading('Precisión numérica')
para('La suma en coma flotante depende del orden y no es exactamente asociativa. '
     'La API permite diferencias de redondeo entre recorridos. Por eso se compara con '
     'tolerancia; la prueba original usa error absoluto menor que 1E-5. NaN se comprueba '
     'con `Double.isNaN`, nunca con `valor == Double.NaN`. [4]')

page('04 / Implementación 2', 'Nombre más frecuente',
     'La reducción construye frecuencias por partición y suma los mapas.')
code(method('mostCommonFirstNameOfInactiveStudentsParallelStream'))
para('El mapa asocia cada nombre con un arreglo de una posición, `int[1]`. Esa celda '
     'contiene su frecuencia. Usar un contador primitivo mutable evita crear un Integer '
     'nuevo en cada incremento. La modificación se limita al resultado parcial de la '
     'reducción; los estudiantes y su arreglo no cambian.', small=True)

page('05 / Reducción y seguridad', 'Cómo se cuentan los nombres',
     'La seguridad está en el aislamiento de los acumuladores, no en HashMap.')
table(['Parte de collect', 'Qué hace la implementación'], [
    ['Supplier', '`HashMap<String, int[]>::new` crea un mapa vacío para una partición.'],
    ['Accumulator', 'Busca el nombre una vez. Si es nuevo, inicia su contador en 1; '
     'si existe, incrementa la celda.'],
    ['Combiner', 'Recorre el mapa derecho y suma sus frecuencias al izquierdo. '
     'Si una clave no existía, incorpora su contador.'],
    ['Selección final', 'Recorre las entradas del mapa combinado y toma la mayor '
     'frecuencia con `max`. Sin entradas, devuelve null.'],
], [115, W - 115])
heading('Invariante que explica la corrección')
para('Después de procesar una partición P, el contador de cada nombre x es exactamente '
     'la cantidad de estudiantes inactivos de P cuyo nombre es x. Para dos particiones '
     'disjuntas, la frecuencia combinada es f(P1, x) + f(P2, x). El mapa vacío funciona '
     'como identidad y la suma de frecuencias es asociativa. [3]')
para('Ejemplo: {Ana: 2, Luis: 1} combinado con {Ana: 1, Eva: 2} produce '
     '{Ana: 3, Luis: 1, Eva: 2}. El máximo por frecuencia es Ana. No se debe calcular '
     'la moda global eligiendo simplemente una de las modas locales.')
heading('Por qué no hay una carrera de datos')
para('La reducción de tres argumentos usa contenedores separados y los combina de '
     'forma controlada. El mismo mapa o contador parcial no se incrementa simultáneamente '
     'desde tareas independientes. HashMap e int[] no son seguros para escritura '
     'concurrente arbitraria; usarlos en un `forEach` paralelo con un mapa externo '
     'compartido sí introduciría un problema. [2, 3]')
heading('Empates y alternativas')
para('El imperativo recorre un HashMap, que no define orden de iteración. No hay una regla '
     'de desempate en la guía: se devuelve un nombre de frecuencia máxima; ante empate, '
     'ambas versiones pueden elegir nombres distintos. La comparación exacta se exige '
     'cuando hay una moda única. No se añadió un desempate alfabético. [5]')
para('La versión declarativa habitual usa `groupingBy(Student::getFirstName, counting())`. '
     'La reducción implementada expresa ese mismo conteo con menos capas de funciones '
     'por registro. `groupingByConcurrent` puede introducir contención si millones de '
     'registros comparten pocos nombres; no garantiza más velocidad. [6]')

page('06 / Implementación 3', 'Reprobados mayores de 20',
     'Las tres condiciones se deben cumplir al mismo tiempo.')
code(method('countNumberOfFailedStudentsOlderThan20ParallelStream'))
para('La condición exacta es: inactivo Y edad estrictamente mayor que 20 Y nota '
     'estrictamente menor que 65. La definición de reprobado proviene del ejercicio; '
     'no basta una nota baja si el estudiante sigue activo.')
table(['Activo', 'Edad', 'Nota', '¿Se cuenta?', 'Razón'], [
    ['No', '21', '64', 'Sí', 'Cumple las tres condiciones'],
    ['No', '20', '64', 'No', '20 no es mayor que 20'],
    ['No', '20,01', '64', 'Sí', 'La edad es double'],
    ['No', '25', '65', 'No', '65 no es menor que 65'],
    ['Sí', '25', '10', 'No', 'Todavía está activo'],
    ['No', '19', '40', 'No', 'No supera la edad exigida'],
], [52, 52, 48, 77, W - 229])
heading('Por qué count es suficiente')
para('Después del filtro, cada elemento representa exactamente un estudiante que '
     'debe contarse. No hace falta crear una lista de resultados ni mapear cada uno '
     'a 1 manualmente. Si ninguna fila cumple, el conteo es 0.')
heading('Por qué se puede convertir long a int')
para('`count()` devuelve long por contrato de Stream. Aquí la fuente es un único '
     'Student[]: el resultado no puede superar `studentArray.length`, que es int. '
     'La conversión respeta la firma original sin perder información. Para otra '
     'fuente potencialmente mayor, esta justificación no sería válida. [2]')
heading('Identidad y combinación')
para('Cada partición produce un conteo c. El estado inicial es 0 y la combinación es '
     'c1 + c2. Como los subconjuntos del arreglo son disjuntos y los conteos no '
     'superan su longitud total, no hay duplicación ni desbordamiento del resultado.')

page('07 / Ejemplo trabajado', 'Ocho estudiantes, tres consultas',
     'Resuelve primero a mano y luego identifica cada etapa del pipeline.')
table(['#', 'Nombre', 'Edad', 'Nota', 'Activo'], [
    ['1', 'Ana', '18', '90', 'Sí'],
    ['2', 'Luis', '22', '60', 'Sí'],
    ['3', 'Ana', '21', '64', 'No'],
    ['4', 'Ana', '20', '40', 'No'],
    ['5', 'Luis', '25', '65', 'No'],
    ['6', 'Eva', '30', '50', 'No'],
    ['7', 'Ana', '23', '60', 'No'],
    ['8', 'Luz', '24', '10', 'Sí'],
], [35, 150, 95, 95, W - 375])
heading('1. Promedio de activos')
para('Se conservan las filas 1, 2 y 8. Sus edades son 18, 22 y 24. '
     'Suma = 64; cantidad = 3; promedio = 64 / 3 = 21,333333... años. '
     'Las notas 60 y 10 de los activos no influyen en esta consulta.')
heading('2. Nombre más frecuente entre inactivos')
para('Se conservan las filas 3, 4, 5, 6 y 7. Sus nombres son Ana, Ana, Luis, Eva y Ana. '
     'Frecuencias: Ana = 3, Luis = 1, Eva = 1. El resultado es Ana. '
     'Los nombres de las filas activas no intervienen.')
heading('3. Reprobados mayores de 20')
para('Cumplen las filas 3, 6 y 7: el resultado es 3. La fila 4 se excluye por tener '
     'exactamente 20 años; la 5, por nota 65. Las filas 2 y 8 se excluyen por estar '
     'activas, aunque tengan más de 20 años y nota inferior a 65.')
heading('Una partición posible')
para('Dividiendo después de la fila 4, los parciales del promedio son (40, 2) y (24, 1). '
     'Los conteos de reprobados son 1 y 2. Los mapas de nombres inactivos son '
     '{Ana: 2} y {Luis: 1, Eva: 1, Ana: 1}. Combinar estos estados produce los '
     'tres resultados anteriores; la JVM puede elegir otra división.')

page('08 / Complejidad y desempeño', 'Paralelo no implica más rápido',
     'La distribución del trabajo tiene costos y debe medirse.')
para('Sea n la cantidad de estudiantes, k la cantidad de nombres distintos entre '
     'inactivos y q la cantidad de estados parciales que la ejecución crea. '
     'q no tiene por qué ser igual al número de núcleos.')
table(['Consulta', 'Trabajo y estado auxiliar'], [
    ['Promedio', 'Recorrido O(n), estados de tamaño constante por partición. '
     'Evita la lista de activos de la versión imperativa.'],
    ['Reprobados', 'Recorrido O(n), conteos de tamaño constante por partición.'],
    ['Moda', 'Acumulación esperada O(n) con buen hashing y selección O(k). '
     'La fusión añade trabajo: cota gruesa O(qk). Puede mantener hasta O(qk) '
     'entradas parciales, frente a O(k) del mapa final.'],
], [110, W - 110])
heading('Speedup, eficiencia y límite ideal')
para('Speedup S = T_secuencial / T_paralelo. S > 1 indica aceleración; '
     'S < 1 indica ralentización. Eficiencia E = S / p, donde p es el número '
     'de recursos de procesamiento considerados. No se debe confundir p con '
     'la cantidad de particiones.')
para('En el modelo ideal de Amdahl, S(p) = 1 / ((1 - f) + f / p), donde f es '
     'la fracción paralelizable. Por ejemplo, con f = 0,9 y p = 8, el límite '
     'ideal es aproximadamente 4,71. La creación de tareas, las fusiones y '
     'la presión de memoria pueden reducirlo aún más.')
heading('Qué puede frenar esta práctica')
bullet('Pocos registros o muy poco trabajo por registro: coordinar tareas puede costar '
       'más que recorrer el arreglo secuencialmente.')
bullet('Acceso a objetos y memoria: más hilos pueden saturar el ancho de banda; '
       'más núcleos no garantizan una reducción proporcional del tiempo.')
bullet('Muchos nombres diferentes: se crean más entradas y la fusión de mapas crece. '
       'Pocos nombres pueden favorecer mapas locales, sin escrituras compartidas.')
heading('Cómo interpretar las pruebas originales')
para('Exigen S > 1,2 para promedio y reprobados y S >= 0,5 × procesadores para '
     'la moda. Usan currentTimeMillis, pocas repeticiones y no aíslan calentamiento '
     'JIT, recolección de basura ni carga del sistema. Son criterios del ejercicio; '
     'no constituyen una garantía universal de rendimiento.')

page('09 / Validación y reproducción', 'Qué se comprobó',
     'La verificación conserva las pruebas entregadas y añade casos de frontera.')
table(['Suite', 'Resultado de la ejecución final'], [
    ['Original', '6 pruebas, 0 fallos, 0 ignoradas; 819 ms en total. '
     'Incluye 3 pruebas de corrección y 3 de rendimiento.'],
    ['Adicional', '15 pruebas, 0 fallos, 0 ignoradas; 61 ms en total. '
     'Una prueba compara 200 arreglos pseudoaleatorios.'],
    ['Entorno', 'OpenJDK 27, macOS aarch64; 10 procesadores visibles; '
     'paralelismo del commonPool = 9. Compilación con --release 8.'],
], [105, W - 105])
para('Los tiempos anteriores corresponden a suites completas, incluyendo generación '
     'de datos y aserciones. No son tiempos individuales de los métodos ni permiten '
     'calcular su speedup. El registro exacto está en `verificacion/resultados.txt`.', small=True)
heading('Cobertura de las pruebas adicionales')
para('Arreglo vacío, todos activos, todos inactivos, un solo estudiante, edades '
     'fraccionarias, edad exactamente 20, nota exactamente 65, activo con nota baja, '
     'moda solo de inactivos, mayúsculas, empates y colisiones de hash, integridad '
     'del arreglo y ausencia de estado acumulado entre llamadas.')
para('La comparación aleatoria usa semilla 20261109, longitudes entre 0 y 3000 y '
     'edades entre 0 y 100. Promedio: tolerancia 1E-9 o NaN. Conteo: igualdad '
     'exacta. Moda: frecuencia máxima, e igualdad con el imperativo cuando el máximo es único.')
heading('Ejecutar desde practica_2')
code('bash verificacion/verificar.sh')
para('Requiere JDK 8 o posterior y Bash. Usa junit-4.12.jar y hamcrest-core-1.3.jar '
     'ya incluidos. Compila en una carpeta temporal, ejecuta ambas suites, elimina '
     'los .class temporales y guarda el resultado. Si alguna prueba falla, sale '
     'con código distinto de cero. No necesita descargar dependencias.')
heading('Variación observada y entorno Maven')
para('La primera implementación con un collector estándar tuvo una ejecución con '
     'S = 4,612 para moda frente al mínimo 5,0. Ese registro se conserva en '
     '`verificacion/historial/01-collector-estandar.txt`. Tras cambiar la reducción '
     'pasaron las 21 pruebas. Esto no garantiza el mismo rendimiento en otra ejecución.')
para('No se modificó pom.xml. El intento Maven offline no pudo abrir un archivo '
     'de bloqueo en la caché local ~/.m2. La comprobación se realizó directamente '
     'con javac y JUnit. La compatibilidad de API Java 8 se comprobó al compilar; '
     'la ejecución se hizo en Java 27, no en una JVM 8.', small=True)


def qa(question, answer):
    heading(question)
    para(answer)


page('10 / Preguntas de sustentación', 'Fundamentos y promedio',
     'Preguntas probables con respuestas breves que puedes ampliar oralmente.')
qa('1. ¿Qué diferencia hay entre un arreglo y un stream?',
   'El arreglo almacena estudiantes; el stream define su procesamiento. Filtrar no '
   'elimina estudiantes del arreglo. Cada consulta crea un stream nuevo porque el '
   'anterior queda consumido después de su operación terminal.')
qa('2. ¿Qué cambia al llamar parallel()?',
   'Se habilita la ejecución paralela del pipeline. La JVM divide y planifica '
   'trabajo; no se garantiza un hilo por elemento ni una aceleración fija.')
qa('3. ¿Por qué filter y mapToDouble son intermedias?',
   'Devuelven otro stream y no producen todavía el valor final. El recorrido se '
   'activa con average, collect o count. Esta evaluación diferida permite fusionar '
   'operaciones durante el procesamiento.')
qa('4. ¿Qué significa Student::getAge?',
   'Es una referencia al método de instancia que equivale a s -> s.getAge(). '
   'mapToDouble recibe una función que transforma cada Student en un double.')
qa('5. ¿Por qué no mapToInt para las edades?',
   'Student almacena la edad como double. Convertir a int truncaría fracciones y '
   'podría cambiar tanto el promedio como la frontera de edad 20.')
qa('6. ¿Por qué no devolver cero si no hay activos?',
   'La referencia calcula 0.0 / 0.0 y devuelve NaN. Cero sería una edad media '
   'definida y cambiaría el comportamiento solicitado. Por eso se usa orElse(Double.NaN).')
qa('7. ¿Se pueden promediar directamente los promedios parciales?',
   'Solo si las particiones tienen igual cantidad de elementos seleccionados. '
   'En general hay que combinar sumas y cantidades, o ponderar cada promedio '
   'por su cantidad antes de dividir por el total.')
qa('8. ¿Por qué los doubles no se comparan siempre con ==?',
   'El orden de suma puede variar y provocar redondeo distinto. Se usa una '
   'tolerancia adecuada al dominio; NaN requiere Double.isNaN. La precisión '
   'numérica y la corrección de la selección son aspectos diferentes.')

page('11 / Preguntas de sustentación', 'Moda, reducción y concurrencia',
     'Estas preguntas explican las decisiones de la implementación real.')
qa('9. ¿Cuáles son los tres argumentos de collect?',
   'Supplier: mapa vacío. Accumulator: incorporar un estudiante incrementando '
   'su nombre. Combiner: unir dos mapas sumando frecuencias por clave. Son '
   'la creación, acumulación y combinación del estado parcial.')
qa('10. ¿Por qué el contador es int[] y no Integer?',
   'Integer es inmutable: incrementarlo requiere obtener otro valor envuelto. '
   'int[1] ofrece una celda mutable por nombre y partición. El arreglo de una '
   'posición es un contenedor del contador, no una lista de estudiantes.')
qa('11. ¿Cómo puede ser seguro usar HashMap en paralelo?',
   'Porque los mapas parciales están aislados y collect controla su combinación. '
   'HashMap sigue sin ser seguro para escritura concurrente arbitraria. Compartir '
   'un mapa externo entre todas las lambdas sería otro diseño y tendría carreras.')
qa('12. ¿Por qué la combinación debe ser asociativa?',
   'La planificación puede cambiar el agrupamiento de los resultados parciales. '
   'Sumar conteos por clave conserva el resultado al reagruparlos. Restar '
   'frecuencias o elegir solo una moda parcial no cumple esa propiedad.')
qa('13. ¿Por qué no tomar la moda de las modas locales?',
   'Se pierde información. Si A tiene Ana: 6, Eva: 5 y B tiene Luis: 6, Eva: 5, '
   'las modas locales son Ana y Luis; la moda global es Eva con 10. Se deben '
   'conservar las frecuencias de todas las claves hasta combinarlas.')
qa('14. ¿Qué pasa si hay empate o no hay inactivos?',
   'Sin inactivos, el mapa queda vacío y se devuelve null. Con empate se '
   'devuelve una moda válida: HashMap no promete orden. Una regla alfabética '
   'requeriría acordar un contrato adicional y un comparador diferente.')
qa('15. ¿Por qué max usa un stream secuencial?',
   'El recorrido costoso sobre los n estudiantes ya fue paralelo. El máximo '
   'recorre solo k nombres distintos; con pocos nombres, lanzar otra '
   'reducción paralela puede añadir más coordinación que trabajo útil.')
qa('16. ¿groupingByConcurrent sería siempre mejor?',
   'No. Una acumulación compartida puede concentrar escrituras en pocas '
   'claves y generar contención. Hay que medir considerando cardinalidad, '
   'tamaño de entrada y costo de fusionar mapas locales.')

page('12 / Preguntas, ejercicios y fuentes', 'Defender y extender la solución',
     'Comprueba que puedes justificar fronteras, tipos y rendimiento.')
qa('17. ¿Un activo con nota 40 se cuenta como reprobado aquí?',
   'No. Debe ser inactivo, tener edad > 20 y nota < 65. Tampoco se cuentan '
   'la edad exactamente 20 ni la nota exactamente 65.')
qa('18. ¿Por qué count devuelve long y el método int?',
   'Stream admite fuentes grandes y count usa long. Esta fuente es un arreglo '
   'con longitud int, por lo que el conteo cabe en la firma exigida.')
qa('19. ¿Qué es una condición de carrera en este contexto?',
   'Dos tareas leen el mismo contador y ambas escriben su incremento, '
   'perdiendo una actualización. Un contador externo usado desde forEach '
   'paralelo puede sufrirla; la reducción con estados aislados la evita.')
qa('20. ¿Cómo demostrarías que paralelo mejora el tiempo?',
   'Verificaría resultados, calentaría la JVM, consumiría los resultados para '
   'evitar eliminación de trabajo, usaría alta resolución, varias mediciones '
   'y tamaños, y reportaría entorno y dispersión. Un único tiempo no basta.')
heading('Tres ejercicios rápidos y sus respuestas')
para('A. Edades activas 18,5 y 21,5; un inactivo de 99: promedio = 20. '
     'B. Inactivos (20, 64), (21, 65), (21, 64): se cuenta 1. '
     'C. Si una prueba exige S >= 5 y mide 4,8, puede fallar por rendimiento '
     'aunque los resultados sean correctos; primero hay que distinguir ambas causas.')
heading('Fuentes y material utilizado')
para('Guía del Ejercicio 2 y fuentes locales Student.java, StudentAnalytics.java '
     'y StudentAnalyticsTest.java. Referencias oficiales de Java 8 consultadas '
     'el 9 de noviembre de 2026:', small=True)
refs = [
    ('1', 'Paquete java.util.stream: pipeline, evaluación y reducción',
     'https://docs.oracle.com/javase/8/docs/api/java/util/stream/package-summary.html'),
    ('2', 'Stream: filter, collect, count y contratos de uso',
     'https://docs.oracle.com/javase/8/docs/api/java/util/stream/Stream.html'),
    ('3', 'Collector: acumulación, aislamiento e identidad',
     'https://docs.oracle.com/javase/8/docs/api/java/util/stream/Collector.html'),
    ('4', 'DoubleStream: average, vacío y precisión',
     'https://docs.oracle.com/javase/8/docs/api/java/util/stream/DoubleStream.html'),
    ('5', 'HashMap: orden y sincronización',
     'https://docs.oracle.com/javase/8/docs/api/java/util/HashMap.html'),
    ('6', 'Collectors: groupingBy, counting y reducción concurrente',
     'https://docs.oracle.com/javase/8/docs/api/java/util/stream/Collectors.html'),
    ('7', 'ForkJoinPool: commonPool y work-stealing',
     'https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ForkJoinPool.html'),
    ('8', 'OpenJDK: tareas de streams sobre CountedCompleter',
     'https://github.com/openjdk/jdk8u/blob/master/jdk/src/share/classes/java/util/stream/AbstractTask.java'),
]
for num, label, url in refs:
    story.append(Paragraph(f'[{num}] <link href="{url}" color="#007E83">'
                           f'{html.escape(label)}</link>', STYLES['small']))
    markdown.append(f'[{num}] [{label}]({url})\n')


def decorate(canvas, doc):
    canvas.saveState()
    width, height = doc.pagesize
    canvas.setStrokeColor(LINE)
    canvas.line(57, height - 40, width - 57, height - 40)
    canvas.setFont('Strong', 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(57, height - 31, 'COMPUTACIÓN PARALELA Y DISTRIBUIDA')
    canvas.setFont('Body', 8)
    canvas.drawRightString(width - 57, height - 31, 'PRÁCTICA 02')
    canvas.line(57, 42, width - 57, 42)
    canvas.drawString(57, 29, 'Solución explicada y guía de sustentación | 09.11.2026')
    canvas.drawRightString(width - 57, 29, f'{doc.page} / {page_count}')
    canvas.restoreState()


target = OUTPUT / 'Practica_2_guia_de_estudio.pdf'
doc = SimpleDocTemplate(str(target), pagesize=(595.28, 841.89),
                        rightMargin=57, leftMargin=57, topMargin=61,
                        bottomMargin=58, title='Práctica 2 - Streams paralelos de Java',
                        author='Material de estudio de la práctica',
                        subject='Solución, teoría y preguntas de sustentación',
                        pageCompression=1)
doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
(ROOT / 'informe' / 'guia_estudio.md').write_text('\n'.join(markdown), encoding='utf-8')
print(f'PDF generado: {target}')
print(f'Páginas previstas: {page_count}')
