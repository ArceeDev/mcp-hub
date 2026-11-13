# Caso de uso con el kit de prueba (para demo, post o charla)
**Situación:** Asesoría con 30 clientes en ContaSol. Cada mes descarga ~45 Norma 43 (varios bancos por cliente) y una persona pica los apuntes: ~10 min por extracto ≈ **7,5 h/mes**.

**Con Flint (kit en `/mnt/project-files/kit-prueba-despacho/` y https://mcp.keyflint.dev/kit-prueba/):**
1. Arrastra los 45 ficheros en /norma43-a-contasol/ y escribe la 572 de cada banco.
2. Flint comprueba saldo inicial + movimientos = saldo final y los totales del registro 33. Los que no cuadran se rechazan sin cobrar.
3. Descarga un ZIP con un APU.ods por extracto, asientos numerados seguidos.
4. Importa en ContaSol: Utilidades > Importaciones > Apuntes.
5. Revisa solo los marcados REVISAR_555 (con reglas, normalmente < 10 %).

**Resultado esperado:** de 7,5 h a ~45 min de revisión. Coste: 45 × 3 créditos = 135 créditos ≈ 7 € (dentro del Plan Despacho Básico, 2.500 créditos/mes).

**Cifras a validar con el piloto real** (no publicar como hecho hasta medirlas): minutos por extracto actuales, % que acaba en 555, errores de importación.
