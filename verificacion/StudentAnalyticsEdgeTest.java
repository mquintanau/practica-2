package co.edu.unal.paralela;

import java.util.HashMap;
import java.util.Map;
import java.util.Random;
import junit.framework.TestCase;

/** Pruebas adicionales; no reemplazan ni modifican las pruebas de la guía. */
public final class StudentAnalyticsEdgeTest extends TestCase {
    private final StudentAnalytics analytics = new StudentAnalytics();

    private Student student(String name, double age, int grade, boolean active) {
        return new Student(name, "Prueba", age, grade, active);
    }

    public void testEmptyArray() {
        Student[] data = {};
        assertTrue(Double.isNaN(analytics.averageAgeOfEnrolledStudentsParallelStream(data)));
        assertNull(analytics.mostCommonFirstNameOfInactiveStudentsParallelStream(data));
        assertEquals(0, analytics.countNumberOfFailedStudentsOlderThan20ParallelStream(data));
    }

    public void testAllActive() {
        Student[] data = {student("Ana", 18, 10, true), student("Luis", 24, 90, true)};
        assertEquals(21.0, analytics.averageAgeOfEnrolledStudentsParallelStream(data), 0.0);
        assertNull(analytics.mostCommonFirstNameOfInactiveStudentsParallelStream(data));
        assertEquals(0, analytics.countNumberOfFailedStudentsOlderThan20ParallelStream(data));
    }

    public void testAllInactive() {
        Student[] data = {student("Ana", 22, 64, false), student("Ana", 24, 50, false)};
        assertTrue(Double.isNaN(analytics.averageAgeOfEnrolledStudentsParallelStream(data)));
        assertEquals("Ana", analytics.mostCommonFirstNameOfInactiveStudentsParallelStream(data));
        assertEquals(2, analytics.countNumberOfFailedStudentsOlderThan20ParallelStream(data));
    }

    public void testFractionalAgesAndActiveFilter() {
        Student[] data = {student("Ana", 18.5, 80, true), student("Luis", 21.25, 90, true),
                student("Eva", 90, 50, false)};
        assertEquals(19.875, analytics.averageAgeOfEnrolledStudentsParallelStream(data), 1E-12);
    }

    public void testStrictAgeBoundary() {
        Student[] data = {student("Ana", 19.99, 64, false), student("Ana", 20, 64, false),
                student("Ana", 20.0001, 64, false)};
        assertEquals(1, analytics.countNumberOfFailedStudentsOlderThan20ParallelStream(data));
    }

    public void testStrictGradeBoundary() {
        Student[] data = {student("Ana", 21, 64, false), student("Luis", 21, 65, false),
                student("Eva", 21, 66, false)};
        assertEquals(1, analytics.countNumberOfFailedStudentsOlderThan20ParallelStream(data));
    }

    public void testActiveStudentWithLowGradeIsExcluded() {
        Student[] data = {student("Ana", 25, 10, true), student("Luis", 25, 10, false)};
        assertEquals(1, analytics.countNumberOfFailedStudentsOlderThan20ParallelStream(data));
    }

    public void testModeUsesOnlyInactiveStudents() {
        Student[] data = {student("Ana", 20, 80, true), student("Ana", 20, 80, true),
                student("Ana", 20, 80, true), student("Eva", 20, 80, false),
                student("Eva", 21, 80, false), student("Luis", 22, 80, false)};
        assertEquals("Eva", analytics.mostCommonFirstNameOfInactiveStudentsParallelStream(data));
    }

    public void testNamesAreCaseSensitive() {
        Student[] data = {student("Ana", 20, 80, false), student("ana", 20, 80, false),
                student("ana", 20, 80, false)};
        assertEquals("ana", analytics.mostCommonFirstNameOfInactiveStudentsParallelStream(data));
    }

    public void testTiedModeAndHashCollision() {
        // "FB" y "Ea" tienen el mismo hashCode; cualquiera es una moda válida.
        Student[] data = {student("FB", 22, 80, false), student("Ea", 22, 80, false),
                student("FB", 22, 80, false), student("Ea", 22, 80, false),
                student("Otro", 22, 80, false)};
        String mode = analytics.mostCommonFirstNameOfInactiveStudentsParallelStream(data);
        assertTrue("FB".equals(mode) || "Ea".equals(mode));
    }

    public void testSourceArrayIsUnchanged() {
        Student[] data = {student("Ana", 21, 64, false), student("Eva", 19, 90, true)};
        Student[] copy = data.clone();
        analytics.averageAgeOfEnrolledStudentsParallelStream(data);
        analytics.mostCommonFirstNameOfInactiveStudentsParallelStream(data);
        analytics.countNumberOfFailedStudentsOlderThan20ParallelStream(data);
        for (int i = 0; i < data.length; i++) {
            assertSame(copy[i], data[i]);
        }
    }

    public void testSingleActiveStudent() {
        Student[] data = {student("Ana", 20.5, 64, true)};
        assertEquals(20.5, analytics.averageAgeOfEnrolledStudentsParallelStream(data), 0.0);
        assertNull(analytics.mostCommonFirstNameOfInactiveStudentsParallelStream(data));
        assertEquals(0, analytics.countNumberOfFailedStudentsOlderThan20ParallelStream(data));
    }

    public void testSingleInactiveStudent() {
        Student[] data = {student("Ana", 20.5, 64, false)};
        assertTrue(Double.isNaN(analytics.averageAgeOfEnrolledStudentsParallelStream(data)));
        assertEquals("Ana", analytics.mostCommonFirstNameOfInactiveStudentsParallelStream(data));
        assertEquals(1, analytics.countNumberOfFailedStudentsOlderThan20ParallelStream(data));
    }

    public void testRepeatedCallsDoNotShareState() {
        Student[] first = {student("Ana", 21, 10, false)};
        Student[] second = {student("Eva", 18, 90, true)};
        for (int i = 0; i < 12; i++) {
            assertEquals("Ana", analytics.mostCommonFirstNameOfInactiveStudentsParallelStream(first));
            assertNull(analytics.mostCommonFirstNameOfInactiveStudentsParallelStream(second));
            assertEquals(1, analytics.countNumberOfFailedStudentsOlderThan20ParallelStream(first));
            assertEquals(0, analytics.countNumberOfFailedStudentsOlderThan20ParallelStream(second));
        }
    }

    public void testRandomizedEquivalence() {
        Random random = new Random(20261109L);
        String[] names = {"Ana", "Luis", "Eva", "FB", "Ea", "ana", "Luz"};
        for (int sample = 0; sample < 200; sample++) {
            Student[] data = new Student[random.nextInt(3001)];
            Map<String, Integer> counts = new HashMap<String, Integer>();
            for (int i = 0; i < data.length; i++) {
                String name = names[random.nextInt(names.length)];
                boolean active = random.nextBoolean();
                data[i] = student(name, random.nextDouble() * 100,
                        random.nextInt(101), active);
                if (!active) {
                    counts.put(name, counts.containsKey(name) ? counts.get(name) + 1 : 1);
                }
            }
            double expected = analytics.averageAgeOfEnrolledStudentsImperative(data);
            double actual = analytics.averageAgeOfEnrolledStudentsParallelStream(data);
            if (Double.isNaN(expected)) {
                assertTrue(Double.isNaN(actual));
            } else {
                assertEquals(expected, actual, 1E-9);
            }
            assertEquals(analytics.countNumberOfFailedStudentsOlderThan20Imperative(data),
                    analytics.countNumberOfFailedStudentsOlderThan20ParallelStream(data));
            String mode = analytics.mostCommonFirstNameOfInactiveStudentsParallelStream(data);
            if (counts.isEmpty()) {
                assertNull(mode);
            } else {
                int maxCount = java.util.Collections.max(counts.values());
                assertTrue(counts.containsKey(mode));
                assertEquals(maxCount, counts.get(mode).intValue());
                long winners = counts.values().stream().filter(c -> c == maxCount).count();
                if (winners == 1) {
                    assertEquals(analytics.mostCommonFirstNameOfInactiveStudentsImperative(data), mode);
                }
            }
        }
    }
}
