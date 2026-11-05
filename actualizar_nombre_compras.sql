SET XACT_ABORT ON;
SET QUOTED_IDENTIFIER ON;
BEGIN TRANSACTION;
UPDATE dbo.usuarios
SET nombre_completo=N'Alberto Enrique Gomez Lopez', updated_at=GETDATE()
WHERE username='encargado_comp';
IF @@ROWCOUNT <> 1
BEGIN
    ROLLBACK;
    THROW 50001, 'Se esperaba una sola cuenta de compras.', 1;
END;
COMMIT;
SELECT id,username,nombre_completo FROM dbo.usuarios WHERE username='encargado_comp';
