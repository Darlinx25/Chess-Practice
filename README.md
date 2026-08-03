# Chess-Practice — Entrenamiento táctico

Aplicación de escritorio (Python + PySide6) para entrenar táctica de ajedrez con
sesiones por ciclos de repetición.

La aplicación usa los 1499 puzzles tácticos del dataset público de Lichess
(`lichess_db_puzzle.csv`, [puzzle DB](https://database.lichess.org/)) y los sirve en
sesiones por bloques dentro de ciclos repetidos (hasta 7 ciclos de repetición).
Cada puzzle tiene un bando a resolver y una solución; los movimientos del usuario se
validan contra esa solución y el rival responde automáticamente con la jugada siguiente.

## Requisitos

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recomendado) o `pip`
- python-chess y PySide6 (ver `pyproject.toml`)

## Instalación

```bash
uv sync
```

## Uso

```bash
uv run python app/main.py
```

### Entrenar

- La pestaña **Inicio** te lleva de vuelta al tablero con el ejercicio en curso
  (o arranca la sesión la primera vez). Al cerrar y volver a abrir la app, retomás
  el ejercicio donde lo dejaste.
- Cada ejercicio muestra una posición. Tu bando (blanco/negro) está indicado por el
  triángulo ▲/▼ y mueve primero; el rival contesta con la siguiente jugada de la solución.
- Movés con clic o arrastrando la pieza.
  - Jugada correcta → flash verde y el rival contesta.
  - Jugada incorrecta → se deshace, flash rojo y sonido de error.
- El ejercicio se **resuelve** cuando completás la secuencia ganadora de la solución
  (o das mate). Ahí se muestra la solución completa.
- **Pista**: muestra la siguiente jugada de la solución para la posición actual.
- **< / >**: retrocedé y avanzá las jugadas del ejercicio (las tuyas y las del
  rival) para revisar la línea; al volver al presente podés seguir jugando.
- **Repetir**: reinicia el ejercicio actual desde el principio.
- **Lista de la izquierda**: ejercicios de la sesión actual, paginados de a 10.
  Clic en uno para saltar directo a ese ejercicio.
- **🎲 Puzles al azar**: modo casual. Cada puzzle se elige al azar y no se guarda
  nada; al pasar uno sale otro al azar. La lista de la izquierda muestra los que ya
  jugaste en esta tanda para poder volver a hacerlos con un clic.

Colores del tablero:

- Verde → casillas de destino legal de la pieza seleccionada.
- Azul → pieza seleccionada / arrastrada.
- Ámbar → casillas de origen y destino del último movimiento.
- Púrpura → casillas de la jugada mostrada por **Pista**.
- Rojo/verde (flash) → jugada incorrecta / correcta.

### Progreso

Resumen de ciclos, sesiones recientes, ejercicios problemáticos y precisión general.
Incluye un botón para reiniciar todo el progreso.

## Datos

- `lichess_db_puzzle.csv`: puzzles de Lichess (FEN, Moves, Rating, Themes, …). Descargá
  la versión completa desde https://database.lichess.org/ y reemplazá el archivo.
- `scripts/build_from_lichess.py`: genera `data/exercises.json` a partir del CSV
  (aplica la jugada previa del rival, asigna bando y dificultad por rating).
- `data/exercises.json`: los 1499 ejercicios generados (FEN, bando, movimientos de la
  solución, dificultad, rating, temas).
- `data/chess_practice.db`: SQLite con sesiones e intentos (se crea automáticamente).

Dificultad por rating: fácil < 1000, intermedia 1000–1500, avanzada ≥ 1500.

## Estructura

```
app/
  config.py        # rutas y parámetros del método
  exercises.py     # carga de ejercicios
  storage.py       # SQLite (sesiones, intentos, ajustes)
  coach.py         # lógica de bloques/repeticiones/ciclos
  sounds.py        # efectos de sonido generados en runtime
  ui/
    board_widget.py    # tablero interactivo (coordenadas, drag & drop, flashes)
    session_view.py    # vista de entrenamiento
    sidebar.py         # lista lateral de ejercicios (sesiones paginadas)
    summary_view.py    # vista de progreso
    main_window.py     # ventana principal
    style.py           # hoja de estilos QSS (tema oscuro)
  main.py          # punto de entrada
```

## Licencias

- Chess-Practice: **GPL-3.0** (ver `LICENSE`).
- Python-chess (GPL-3.0+), piezas de Cburnett (CC-BY-SA-3.0 / GPL-2+),
  puzzles de Lichess (CC0), PySide6 (LGPL-3.0) y PyInstaller (GPL-2+ con
  excepción). Detalles en `THIRD_PARTY_NOTICES.md`.
