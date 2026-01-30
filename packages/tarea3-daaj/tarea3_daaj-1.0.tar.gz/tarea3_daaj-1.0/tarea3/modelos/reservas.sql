BEGIN TRANSACTION;

-- =========================
-- BORRAR TABLAS (HIJA → PADRES)
-- =========================
DROP TABLE IF EXISTS reservas;
DROP TABLE IF EXISTS tipos_reservas;
DROP TABLE IF EXISTS tipos_cocina;
DROP TABLE IF EXISTS salones;

-- =========================
-- CREAR TABLAS PADRE
-- =========================
CREATE TABLE salones (
    salon_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(255) NOT NULL
);

CREATE TABLE tipos_reservas (
    tipo_reserva_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(255) NOT NULL,
    requiere_jornadas TINYINT NOT NULL DEFAULT 0,
    requiere_habitaciones TINYINT NOT NULL DEFAULT 0
);

CREATE TABLE tipos_cocina (
    tipo_cocina_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(255) NOT NULL
);

-- =========================
-- CREAR TABLA HIJA
-- =========================
CREATE TABLE reservas (
    reserva_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_reserva_id INTEGER NOT NULL,
    salon_id INTEGER NOT NULL,
    tipo_cocina_id INTEGER NOT NULL,
    persona VARCHAR(255) NOT NULL,
    telefono VARCHAR(25) NOT NULL,
    fecha DATE NOT NULL,
    ocupacion INTEGER NOT NULL,
    jornadas INTEGER NOT NULL,
    habitaciones INTEGER NOT NULL DEFAULT 0,
    UNIQUE (salon_id, fecha),
    FOREIGN KEY (tipo_reserva_id) REFERENCES tipos_reservas(tipo_reserva_id),
    FOREIGN KEY (tipo_cocina_id) REFERENCES tipos_cocina(tipo_cocina_id),
    FOREIGN KEY (salon_id) REFERENCES salones(salon_id)
);

-- =========================
-- INSERTAR TABLAS PADRE
-- =========================
INSERT INTO salones (salon_id, nombre) VALUES
(1, 'Salón Habana'),
(2, 'Otro Salón');

INSERT INTO tipos_reservas (tipo_reserva_id, nombre, requiere_jornadas, requiere_habitaciones) VALUES
(1, 'Banquete', 0, 0),
(2, 'Jornada', 0, 0),
(3, 'Congreso', 1, 1);

INSERT INTO tipos_cocina (tipo_cocina_id, nombre) VALUES
(1, 'Bufé'),
(2, 'Carta'),
(3, 'Pedir cita con el chef'),
(4, 'No precisa');

-- =========================
-- INSERTAR TABLA HIJA (AL FINAL)
-- =========================
INSERT INTO reservas
(tipo_reserva_id, salon_id, tipo_cocina_id, persona, telefono, fecha, ocupacion, jornadas, habitaciones)
VALUES
(1,1,1,'David','600123456','2024-12-20',35,0,0),
(2,2,2,'Juan','123456780','2024-11-17',2,0,0),
(1,2,1,'Juan','123456789','2024-11-16',1,0,0),
(2,2,1,'Perico','666778899','2024-11-15',3,0,0),
(1,1,2,'David','111223344','2024-11-20',35,0,0),
(1,1,1,'David','222334455','2024-11-21',3,0,0),
(3,2,3,'Jacinto','333445566','2024-12-21',2,2,0),
(1,1,1,'Jacinto','444556677','2024-10-21',1,0,0),
(1,2,1,'Fernando','555667788','2024-10-21',1,0,0),
(3,1,2,'Luis','645704341','2024-12-01',3,1,1),
(2,1,2,'Azucena','345243654','2024-10-01',5,0,0),
(2,1,2,'Azucena','345243654','2024-10-02',5,0,0);

COMMIT;


