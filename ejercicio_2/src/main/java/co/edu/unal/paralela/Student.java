package co.edu.unal.paralela;

/**
 * Una clase representando un estudiante en un única clase
 */
public final class Student {
    /**
     * Nombre(s) del estudiante.
     */
    private final String firstName;
    /**
     * Apellido(s) del estudiante.
     */
    private final String lastName;
    /**
     * Edad del estudiante.
     */
    private final double age;
    /**
     * Nota que el estudiante ha recibido hasta ahora.
     */
    private final int grade;
    /**
     * Si el estudiante ya está registrado o ya terminó el curso.
     */
    private final boolean isCurrent;

    /**
     * Constructor.
     * @param setFirstName Nombres del estudiante
     * @param setLastName Apellido del estudiante
     * @param setAge Edad del estudiante
     * @param setGrade Nota del estudiante en el curso
     * @param setIsCurrent El estudiante está registrado?
     */
    public Student(final String setFirstName, final String setLastName,
            final double setAge, final int setGrade,
            final boolean setIsCurrent) {
        this.firstName = setFirstName;
        this.lastName = setLastName;
        this.age = setAge;
        this.grade = setGrade;
        this.isCurrent = setIsCurrent;
    }

    /**
     * Recupera los nombres de este estudiante
     * @return Los nombres del estuidante
     */
    public String getFirstName() {
        return firstName;
    }

    /**
     * Recupera los apellidos de este estudiante
     * @return los apellidos del estudiantes
     */
    public String getLastName() {
        return lastName;
    }

    /**
     * Recupera la edad del estudiante.
     * @return Edad del estudiante.
     */
    public double getAge() {
        return age;
    }

    /**
     * Recupera la Nota que el estudiante ha recibido hasta ahora.
     * @return calificación actual del estudiante.
     */
    public int getGrade() {
        return grade;
    }

    /**
     * Revisa si el estudiante está activo, o ya tomó el curso antes.
     * @return verdadero si el estudiante está registrado en la actualidad, falso en cualquier otro caso
     */
    public boolean checkIsCurrent() {
        return isCurrent;
    }
}
