# N1 — decidir() con reglas puras · rama carril/nucleo-sp1-decidir · cuelga de 14837f8 · commit (ver PR) · modelo claude-haiku-5-5 · esfuerzo no visible · ~20 min
Hecho: `normalizar.py` (texto sin acentos, parecido por palabras con difflib, a_base kg→g, l→ml, piezas); `decidir.py` con las 12 reglas en orden y umbrales como constantes; `test_decidir.py` con 14 pruebas.
Prueba de cierre: `py -3 -m unittest ml.validat3b.test_decidir -v` → Ran 14 tests, OK (la misión pedía 13; hay 14 porque la regla 6 y la 7 tienen dos casos cada una).
No hecho / simulado: nada simulado; todo con datos inventados. Sin validar contra datos de 3B (eso es de Datos/N2).
Decisiones propias (revisar): descripción se compara contra product_name con los mismos umbrales que marca; contenido no comparable (unidad desconocida) → revision_manual; validaciones.evidencia_precio = falla en reglas 8, 9 y 10; codigo_barras siempre ok.
Archivos fuera de mi carril que toqué: ninguno.
¿Tocó la base?: no.
Necesito de otro carril: nada (contrato.py importado sin editar).
