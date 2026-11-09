import java.util.concurrent.ForkJoinPool;
import org.junit.runner.JUnitCore;
import org.junit.runner.Result;
import org.junit.runner.notification.Failure;

/** Ejecuta las suites originales y adicionales y conserva sus resultados. */
public final class RunTests {
    public static void main(String[] args) throws Exception {
        System.out.println("Practica 2 - verificacion reproducible");
        System.out.println("Fecha: " + java.time.ZonedDateTime.now(java.time.ZoneId.of("America/Bogota")));
        System.out.println("Java: " + System.getProperty("java.version"));
        System.out.println("VM: " + System.getProperty("java.vm.name"));
        System.out.println("SO: " + System.getProperty("os.name") + " / " + System.getProperty("os.arch"));
        System.out.println("Procesadores disponibles: " + Runtime.getRuntime().availableProcessors());
        System.out.println("Paralelismo commonPool: " + ForkJoinPool.getCommonPoolParallelism());
        int failed = 0;
        for (String name : new String[] {"co.edu.unal.paralela.StudentAnalyticsTest",
                "co.edu.unal.paralela.StudentAnalyticsEdgeTest"}) {
            Result result = JUnitCore.runClasses(Class.forName(name));
            System.out.println("\n" + name + ": " + result.getRunCount() + " pruebas, "
                    + result.getFailureCount() + " fallos, " + result.getIgnoreCount()
                    + " ignoradas; " + result.getRunTime() + " ms");
            for (Failure failure : result.getFailures()) {
                System.out.println(failure.getTrace());
            }
            failed += result.getFailureCount();
        }
        System.out.println("\nRESULTADO: " + (failed == 0 ? "OK" : "FALLO"));
        if (failed != 0) {
            System.exit(1);
        }
    }
}
