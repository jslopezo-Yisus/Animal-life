-- ============================================================
-- ANIMAL-LIFE
-- Base de datos principal
-- ============================================================

CREATE DATABASE IF NOT EXISTS animal_life
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE animal_life;


-- ============================================================
-- 1. ROLES
-- ============================================================

CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    estado BOOLEAN NOT NULL DEFAULT TRUE
);


-- ============================================================
-- 2. USUARIOS
-- ============================================================

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rol_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    correo VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    telefono VARCHAR(20),
    direccion VARCHAR(255),
    estado BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_usuario_rol
        FOREIGN KEY (rol_id)
        REFERENCES roles(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);


-- ============================================================
-- 3. ANIMALES
-- ============================================================

CREATE TABLE IF NOT EXISTS animales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    especie VARCHAR(50) NOT NULL,
    raza VARCHAR(100),
    sexo VARCHAR(20),
    fecha_nacimiento DATE,
    tamano VARCHAR(30),
    color VARCHAR(100),
    descripcion TEXT,
    estado VARCHAR(50) NOT NULL DEFAULT 'Disponible',
    imagen VARCHAR(255),
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);


-- ============================================================
-- 4. ESTADOS DE REPORTE
-- ============================================================

CREATE TABLE IF NOT EXISTS estados_reporte (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(255)
);


-- ============================================================
-- 5. REPORTES
-- ============================================================

CREATE TABLE IF NOT EXISTS reportes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    animal_id INT,
    estado_id INT NOT NULL,
    tipo VARCHAR(100) NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT NOT NULL,
    direccion VARCHAR(255),
    latitud DECIMAL(10, 8),
    longitud DECIMAL(11, 8),
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_reporte_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_reporte_animal
        FOREIGN KEY (animal_id)
        REFERENCES animales(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT fk_reporte_estado
        FOREIGN KEY (estado_id)
        REFERENCES estados_reporte(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);


-- ============================================================
-- 6. EVIDENCIAS
-- ============================================================

CREATE TABLE IF NOT EXISTS evidencias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reporte_id INT NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    ruta_archivo VARCHAR(500) NOT NULL,
    tipo_archivo VARCHAR(100),
    fecha_subida DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_evidencia_reporte
        FOREIGN KEY (reporte_id)
        REFERENCES reportes(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- ============================================================
-- 7. SERVICIOS
-- ============================================================

CREATE TABLE IF NOT EXISTS servicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    precio DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    duracion_minutos INT,
    estado BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 8. CITAS
-- ============================================================

CREATE TABLE IF NOT EXISTS citas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    animal_id INT NOT NULL,
    servicio_id INT NOT NULL,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'Pendiente',
    observaciones TEXT,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_cita_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_cita_animal
        FOREIGN KEY (animal_id)
        REFERENCES animales(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_cita_servicio
        FOREIGN KEY (servicio_id)
        REFERENCES servicios(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);


-- ============================================================
-- 9. ADOPCIONES
-- ============================================================

CREATE TABLE IF NOT EXISTS adopciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    usuario_id INT NOT NULL,
    fecha_solicitud DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_respuesta DATETIME NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'Pendiente',
    observaciones TEXT,

    CONSTRAINT fk_adopcion_animal
        FOREIGN KEY (animal_id)
        REFERENCES animales(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_adopcion_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);


-- ============================================================
-- 10. NOTIFICACIONES
-- ============================================================

CREATE TABLE IF NOT EXISTS notificaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    mensaje TEXT NOT NULL,
    tipo VARCHAR(50),
    leida BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_notificacion_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- ============================================================
-- 11. ACCESOS
-- ============================================================

CREATE TABLE IF NOT EXISTS accesos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    hora_acceso TIME NOT NULL,
    dia_semana TINYINT NOT NULL,
    intentos_fallidos INT NOT NULL DEFAULT 0,
    ubicacion_habitual BOOLEAN NOT NULL DEFAULT TRUE,
    dispositivo_conocido BOOLEAN NOT NULL DEFAULT TRUE,
    acceso_exitoso BOOLEAN NOT NULL DEFAULT FALSE,
    cambio_contrasena_reciente BOOLEAN NOT NULL DEFAULT FALSE,
    amenaza BOOLEAN NOT NULL DEFAULT FALSE,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_acceso_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);


-- ============================================================
-- DATOS INICIALES
-- ============================================================

INSERT IGNORE INTO roles
    (id, nombre, descripcion)
VALUES
    (1, 'Administrador', 'Control general de la plataforma'),
    (2, 'Ciudadano', 'Usuario que utiliza los servicios de Animal-Life'),
    (3, 'Veterinario', 'Profesional encargado de atención veterinaria'),
    (4, 'Tecnico', 'Personal encargado de atender solicitudes'),
    (5, 'Fundacion', 'Personal encargado de la gestión de la fundación');


INSERT IGNORE INTO estados_reporte
    (id, nombre, descripcion)
VALUES
    (1, 'Pendiente', 'Reporte recibido y pendiente de revisión'),
    (2, 'En revisión', 'El reporte está siendo revisado'),
    (3, 'Asignado', 'El reporte fue asignado a un responsable'),
    (4, 'En proceso', 'El reporte está siendo atendido'),
    (5, 'Resuelto', 'El problema fue solucionado'),
    (6, 'Cerrado', 'El proceso fue finalizado');


INSERT IGNORE INTO servicios
    (nombre, descripcion, precio, duracion_minutos)
VALUES
    (
        'Consulta veterinaria',
        'Consulta general para animales domésticos',
        0.00,
        30
    ),
    (
        'Vacunación',
        'Aplicación y control de vacunas',
        0.00,
        20
    ),
    (
        'Desparasitación',
        'Servicio de desparasitación para animales',
        0.00,
        20
    ),
    (
        'Baño',
        'Servicio de higiene para animales',
        0.00,
        45
    ),
    (
        'Peluquería',
        'Servicio de peluquería y cuidado estético',
        0.00,
        60
    ),
    (
        'Atención básica',
        'Atención básica para animales',
        0.00,
        30
    );


-- ============================================================
-- VERIFICACIÓN
-- ============================================================

SHOW TABLES;