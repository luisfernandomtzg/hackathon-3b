# remoto-hackathon-3b.ps1 - control remoto de Claude Code sobre ESTE repo, con MODO DE ESTADO.
#
# Derivado de adme-skills/herramientas/remoto-plantilla.ps1 (metodo, seccion 2.2 punto 17),
# adaptado al Hackathon 3B (S000, 17-nov-2026): UN documento de prompts POR CARRIL
# (docs\prompts-<carril>.md, ids U/N/D/I) en vez de uno por sesion.
#
# Tres usos:
#   .\remoto-hackathon-3b.ps1                    guard de "un dueno por arbol" + lanza el control remoto
#   .\remoto-hackathon-3b.ps1 -SoloDiagnostico   corre el guard, imprime el veredicto y NO lanza nada
#   .\remoto-hackathon-3b.ps1 -Estado -Carril ui   NO lanza nada: calcula EN ESTE MOMENTO donde esta el repo
#                                              y que mision sigue EN ESE CARRIL, y evalua la regla de paro.
#   .\remoto-hackathon-3b.ps1 -Estado            lo mismo para los cuatro carriles. Sale con 0.
#
# -Estado es para el IMPLEMENTADOR: lo corre como PRIMER PASO de cada prompt y pega la salida
# en su acuse (seccion 3.3). Asi el acuse deja de depender de que alguien lea bien un archivo.
# Desde la terminal de Claude Code:
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\remoto-hackathon-3b.ps1 -Estado
#
# Lo que -Estado calcula, cada vez (no guarda nada: un estado guardado envejece, R14):
#   - rama, SHA y si el arbol esta sucio
#   - el documento del carril: docs\prompts-<carril>.md (fijo, no se elige por fecha)
#   - el sello del ESTADO, el campo "siguiente" y las reescrituras
#   - el reporte mas nuevo DE ESE CARRIL (docs\reportes\<letra><n>-*.md) y su hora EFECTIVA: la del commit si el archivo esta
#     commiteado y sin cambios (un merge o checkout reescribe el mtime), el mtime si no
#   - PIERNA 2 de la regla de paro (reporte posterior al sello) y la CONFIRMACION POR CONTENIDO
#     (el "siguiente" ya tiene reporte)
#   - y termina diciendo lo que NO pudo ver.
# La PIERNA 1 (tu entrega anterior de ESTA sesion vs. el sello) no la puede ver ningun script:
# la evalua el implementador con su propio historial.
#
# Opcional - gancho de arranque de sesion (.claude\settings.json del repo), para que la salida
# entre sola al contexto al abrir o reanudar una sesion:
#   { "hooks": { "SessionStart": [ { "matcher": "startup|resume",
#       "hooks": [ { "type": "command",
#         "command": "powershell -NoProfile -ExecutionPolicy Bypass -File \"$CLAUDE_PROJECT_DIR\\remoto-hackathon-3b.ps1\" -Estado" } ] } ] } }
# El gancho es una comodidad, NO la garantia: hay reportes de superficies donde su salida no llega
# al contexto. La garantia es el paso del acuse en cada prompt.
#
# Origen: remoto-talos-v2.ps1 (Talos ERP, 25-ago-2026), del que conserva el guard completo:
#   - no confunde la app de escritorio con un agente
#   - cada remoto DECLARA su arbol con un marcador (PID + StartTime), porque Windows no expone
#     el directorio de trabajo de un proceso
#   - los marcadores rancios se limpian solos; lo que nadie reclama se pregunta (falla CERRADO)
# Este archivo es ASCII a proposito: Windows PowerShell 5.1 lee un .ps1 sin BOM como ANSI.

param(
    [switch]$SoloDiagnostico,
    [switch]$Estado,
    [ValidateSet('ui','nucleo','datos','integrador')]
    [string]$Carril
)

# ====== CONFIGURA - llena esto al copiar la plantilla ==========================
$PROYECTO         = 'Hackathon 3B'    # nombre visible en los avisos
$RAMA_INTEGRACION = 'main'     # la rama de integracion del repo
$REGISTROS_EXTRA  = @()           # registros de scripts anteriores con los que convives,
                                  # p. ej. @('talos-remotos'): sus marcadores se LEEN (y uno rancio
                                  # se limpia igual que los propios); nunca se escribe uno ahi
# ===============================================================================

Set-Location -LiteralPath $PSScriptRoot

$ARBOL           = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$MARCADOR_LOCAL  = Join-Path $ARBOL '.git\remoto-activo.json'
$REGISTRO_DIR    = Join-Path $env:LOCALAPPDATA 'adme-remotos'

# --- E. Modo de estado -------------------------------------------------------
# Todo lo que sigue en esta seccion es de SOLO LECTURA: no escribe, no hace fetch, no lanza nada.

function Get-Minuto([datetime]$t) { return $t.Date.AddHours($t.Hour).AddMinutes($t.Minute) }

$HAY_GIT = [bool](Get-Command git -ErrorAction SilentlyContinue)

function Get-HoraEfectiva($archivo, [string]$arbol) {
    # Hora del commit si el archivo esta commiteado y sin cambios; mtime si no.
    if (-not $HAY_GIT) { return [pscustomobject]@{ Hora = $archivo.LastWriteTime; Fuente = 'mtime' } }
    $rel = $archivo.FullName.Substring($arbol.Length).TrimStart('\','/')
    $sucio  = (git status --porcelain -- $rel 2>$null)
    $commit = (git log -1 --format=%aI -- $rel 2>$null)
    if ($commit -and -not $sucio) {
        try {
            $dt = [datetimeoffset]::Parse($commit, [cultureinfo]::InvariantCulture).LocalDateTime
            return [pscustomobject]@{ Hora = $dt; Fuente = 'commit' }
        } catch { }
    }
    return [pscustomobject]@{ Hora = $archivo.LastWriteTime; Fuente = 'mtime' }
}

$LETRA = @{ ui = 'U'; nucleo = 'N'; datos = 'D'; integrador = 'I' }

function Show-Estado([string]$car) {
    $noVi = New-Object System.Collections.Generic.List[string]
    $paro = New-Object System.Collections.Generic.List[string]
    $ahora = Get-Date

    Write-Output ("ESTADO-REMOTO | {0} | carril {1} | calculado {2}" -f $PROYECTO, $car, $ahora.ToString('yyyy-MM-dd HH:mm:ss'))
    Write-Output ("Arbol      : {0}" -f $ARBOL)

    # -- git
    $rama = $null; $sha = $null
    if ($HAY_GIT) {
        $rama = (git rev-parse --abbrev-ref HEAD 2>$null)
        $sha  = (git rev-parse --short HEAD 2>$null)
    }
    if ($rama) {
        Write-Output ("Rama       : {0} ({1})" -f $rama, $sha)
        $int = (git rev-parse --short ("origin/" + $RAMA_INTEGRACION) 2>$null)
        if ($int) { Write-Output ("Integracion: origin/{0} = {1}   [ref local, SIN fetch: el primer paso del prompt es git fetch]" -f $RAMA_INTEGRACION, $int) }
        else      { $noVi.Add("origin/$RAMA_INTEGRACION (no existe el ref local)") }
        $sucio = @(git status --porcelain 2>$null)
        if ($sucio.Count -gt 0) {
            Write-Output ("Sucio      : {0} archivo(s) sin commitear" -f $sucio.Count)
            $sucio | Select-Object -First 8 | ForEach-Object { Write-Output ("             {0}" -f $_) }
            if ($sucio.Count -gt 8) { Write-Output ("             ... y {0} mas" -f ($sucio.Count - 8)) }
        } else { Write-Output "Sucio      : no (arbol limpio)" }
    } else {
        Write-Output "Rama       : [no se pudo leer git desde aqui]"
        $noVi.Add('git (rama, SHA, arbol sucio, hora de commit de los reportes)')
    }

    # -- el documento del carril (fijo)
    $docs = Join-Path $ARBOL 'docs'
    $L    = $LETRA[$car]
    $ruta = Join-Path $docs ("prompts-{0}.md" -f $car)
    if (-not (Test-Path -LiteralPath $ruta)) {
        Write-Output ("Documento  : NO EXISTE docs\prompts-{0}.md" -f $car)
        Write-Output "VEREDICTO  : SIN DOCUMENTO - no ejecutes nada; pregunta al arquitecto cual es el encargo."
        return
    }
    $top = [pscustomobject]@{ Archivo = (Get-Item -LiteralPath $ruta) }
    Write-Output ("Documento  : docs\{0}" -f $top.Archivo.Name)

    # -- el bloque ESTADO
    $lineas = @([System.IO.File]::ReadAllLines($top.Archivo.FullName, [System.Text.Encoding]::UTF8))
    $idx = -1
    for ($k = 0; $k -lt $lineas.Count; $k++) { if ($lineas[$k] -match '^##\s*ESTADO\b') { $idx = $k; break } }
    $sello = $null; $siguiente = $null; $sigEnLinea = $null; $reescrituras = $null
    if ($idx -lt 0) {
        $paro.Add('el documento no tiene bloque "## ESTADO"')
    } else {
        # El sello vive en la linea del encabezado ("## ESTADO - 2026-11-14 09:30") o en un
        # campo "sello:" del bloque. Se aceptan las dos formas; manda la del encabezado.
        $reFecha = '(\d{4}-\d{2}-\d{2})[ T]+(\d{1,2}:\d{2})'
        $txtSello = $null
        $ms = [regex]::Match($lineas[$idx], $reFecha)
        if ($ms.Success) { $txtSello = $ms.Groups[1].Value + ' ' + $ms.Groups[2].Value.PadLeft(5, '0') }
        $fin = [Math]::Min($lineas.Count - 1, $idx + 40)
        for ($k = $idx + 1; $k -le $fin; $k++) {
            if ($lineas[$k] -match '^#{2,6}\s') { break }
            if (-not $txtSello) {
                $mx = [regex]::Match($lineas[$k], ('^[\s\-\*\|]*sello[\s\*]*[:\|][\s\*]*' + $reFecha), 'IgnoreCase')
                if ($mx.Success) { $txtSello = $mx.Groups[1].Value + ' ' + $mx.Groups[2].Value.PadLeft(5, '0') }
            }
            if (-not $siguiente) {
                # Forma 1: la linea cuyo CAMPO es "siguiente:" ("siguiente con modelo y esfuerzo" no cuenta).
                $mg = [regex]::Match($lineas[$k], '^[\s\-\*\|]*siguiente[\s\*]*[:\|][\s\*]*([UNDI]\d+[a-z]?(?:\.\d+)?|NINGUNO[^*|]*)', 'IgnoreCase')
                if ($mg.Success) { $siguiente = $mg.Groups[1].Value.Trim() }
            }
            if (-not $sigEnLinea) {
                # Forma 2: en linea, como en la plantilla del metodo ("... - siguiente **P3** - ...").
                # Solo se usa si en todo el bloque no hubo un campo "siguiente:".
                $mi = [regex]::Match($lineas[$k], '\bsiguiente[\s\*]+([UNDI]\d+[a-z]?(?:\.\d+)?|NINGUNO[^*|\u00B7]*)', 'IgnoreCase')
                if ($mi.Success) { $sigEnLinea = $mi.Groups[1].Value.Trim() }
            }
            if ($null -eq $reescrituras) {
                $mr = [regex]::Match($lineas[$k], 'reescrituras[^:\d]*:[\s\*]*(\d+)', 'IgnoreCase')
                if ($mr.Success) { $reescrituras = $mr.Groups[1].Value }
            }
        }
        if (-not $siguiente -and $sigEnLinea) { $siguiente = $sigEnLinea }
        if ($txtSello) {
            try { $sello = [datetime]::ParseExact($txtSello, 'yyyy-MM-dd HH:mm', [cultureinfo]::InvariantCulture) } catch { }
        }
        if (-not $sello)     { $paro.Add('no pude leer el sello (AAAA-MM-DD HH:MM) ni en el encabezado "## ESTADO" ni en un campo "sello:"') }
        if (-not $siguiente) { $paro.Add('no pude leer el campo "siguiente" del ESTADO') }
    }
    $selloTxt = '[ilegible]'; if ($sello) { $selloTxt = $sello.ToString('yyyy-MM-dd HH:mm') }
    $sigTxt   = '[ilegible]'; if ($siguiente) { $sigTxt = $siguiente }
    $reTxt    = '?';          if ($null -ne $reescrituras) { $reTxt = $reescrituras }
    Write-Output ("Sello      : {0} | siguiente: {1} | reescrituras: {2}" -f $selloTxt, $sigTxt, $reTxt)

    $mtDoc = $top.Archivo.LastWriteTime
    if ($sello) {
        $ok = 'SI'; if ($sello -gt (Get-Minuto $mtDoc)) { $ok = 'NO - SELLO ADELANTADO (el arquitecto debe reescribirlo)' }
        Write-Output ("mtime doc  : {0} | sello <= mtime: {1}" -f $mtDoc.ToString('yyyy-MM-dd HH:mm:ss'), $ok)
    }

    # -- pierna 2: el reporte mas nuevo contra el sello
    $dirRep = Join-Path $docs 'reportes'
    $reps = @(Get-ChildItem -LiteralPath $dirRep -Filter '*.md' -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match ('^' + $L + '\d') })
    if ($reps.Count -eq 0) {
        Write-Output ("Reporte    : ninguno del carril {0} en docs\reportes" -f $car)
        Write-Output "Pierna 2   : no dispara (no hay reportes)"
    } else {
        $mejor = $null
        foreach ($r in @($reps | Sort-Object LastWriteTime -Descending | Select-Object -First 8)) {
            $h = Get-HoraEfectiva $r $ARBOL
            if (-not $mejor -or $h.Hora -gt $mejor.Hora) { $mejor = [pscustomobject]@{ Archivo = $r; Hora = $h.Hora; Fuente = $h.Fuente } }
        }
        Write-Output ("Reporte    : docs\reportes\{0}" -f $mejor.Archivo.Name)
        Write-Output ("             hora efectiva {0} ({1}) | mtime {2}" -f $mejor.Hora.ToString('yyyy-MM-dd HH:mm:ss'), $mejor.Fuente, $mejor.Archivo.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))
        if ($reps.Count -gt 8) { Write-Output ("             (comparados los 8 mas recientes por mtime, de {0})" -f $reps.Count) }
        if ($sello) {
            if ((Get-Minuto $mejor.Hora) -gt $sello) {
                $min = [int]((Get-Minuto $mejor.Hora) - $sello).TotalMinutes
                Write-Output ("Pierna 2   : DISPARA - el reporte es {0} min POSTERIOR al sello" -f $min)
                $paro.Add('pierna 2: hay un reporte posterior al sello (el documento no se reescribio tras esa entrega)')
            } else {
                Write-Output "Pierna 2   : no dispara (el sello es igual o posterior al reporte mas nuevo)"
            }
        }
    }

    # -- confirmacion por contenido: el "siguiente" ya tiene reporte?
    if ($siguiente -and $siguiente -match '^[UNDI]\d') {
        $siguiente = $siguiente.ToUpper()
        $pr = '^' + [regex]::Escape($siguiente) + '-'
        $ya = @($reps | Where-Object { [regex]::IsMatch($_.Name, $pr, 'IgnoreCase') })
        if ($ya.Count -gt 0) {
            Write-Output ("Contenido  : {0} YA TIENE REPORTE ({1})" -f $siguiente, $ya[0].Name)
            $paro.Add(("contenido: el siguiente ({0}) ya tiene reporte - el ESTADO esta viejo" -f $siguiente))
        } else {
            Write-Output ("Contenido  : {0} todavia no tiene reporte" -f $siguiente)
        }
    }
    Write-Output "Pierna 1   : la evaluas TU - tu entrega anterior de ESTA sesion, es posterior al sello?"

    # -- veredicto
    if ($paro.Count -gt 0) {
        Write-Output "VEREDICTO  : PARO - NO ejecutes nada. Dilo, enumera esta evidencia y detente."
        foreach ($p in $paro) { Write-Output ("             - {0}" -f $p) }
        Write-Output "             Para salir: el arquitecto reescribe el ESTADO (sube el sello) y te lo reenvia."
    } elseif ($siguiente -match '^NINGUNO') {
        Write-Output ("VEREDICTO  : NADA QUE EJECUTAR - siguiente: {0}. Acusalo y detente." -f $siguiente)
    } else {
        Write-Output ("VEREDICTO  : SIGUE - ejecuta {0} de docs\{1}, si la pierna 1 tampoco dispara." -f $siguiente, $top.Archivo.Name)
    }
    $noVi.Add('la pierna 1 (el historial de tu sesion)')
    $noVi.Add('el remoto (no se hizo fetch)')
    $noVi.Add('la zona horaria del sello (se lee como hora local de esta maquina)')
    Write-Output ("No pude ver: {0}" -f ($noVi -join ' ; '))
}

if ($Estado) {
    if ($Carril) { Show-Estado $Carril }
    else {
        foreach ($c in @('integrador','ui','nucleo','datos')) { Show-Estado $c; Write-Output '' }
    }
    exit 0
}

Write-Host ""
Write-Host ("  Control remoto - {0}" -f $PROYECTO) -ForegroundColor Cyan
Write-Host "  ----------------------------" -ForegroundColor DarkGray
if ($SoloDiagnostico) {
    Write-Host "  MODO DIAGNOSTICO - no se lanza nada" -ForegroundColor Magenta
}

# --- 0. Utilidades del marcador ---------------------------------------------

# El nombre del archivo en el registro cruzado sale del arbol, no del azar: dos
# corridas sobre el mismo arbol pisan el mismo archivo a proposito.
function Get-HashArbol([string]$ruta) {
    $norm = $ruta.TrimEnd('\').ToLowerInvariant()
    $md5  = [System.Security.Cryptography.MD5]::Create()
    $b    = $md5.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($norm))
    return (($b | ForEach-Object { $_.ToString('x2') }) -join '').Substring(0, 12)
}

# PID + StartTime SIEMPRE juntos. Windows recicla PIDs: un marcador viejo cuyo
# PID haya sido reasignado reclamaria un proceso ajeno como propio, en silencio.
# El StartTime es lo que hace que esa confusion sea imposible.
function Test-MarcadorVivo($m) {
    $p = Get-Process -Id $m.pid -ErrorAction SilentlyContinue
    if (-not $p) {
        return [pscustomobject]@{ Vivo = $false; Verificado = $true; Motivo = 'el PID ya no existe' }
    }
    $inicio = $null
    try { $inicio = $p.StartTime.ToString('o') } catch { }
    if (-not $inicio) {
        # No se pudo leer StartTime (permisos). No se puede verificar, asi que
        # NO explica procesos ajenos: se cae al cajon de "nadie lo reclama" y
        # se pregunta. Falla CERRADO en las dos direcciones.
        return [pscustomobject]@{ Vivo = $true; Verificado = $false; Motivo = 'StartTime no legible' }
    }
    if ($inicio -ne $m.inicio) {
        return [pscustomobject]@{ Vivo = $false; Verificado = $true; Motivo = 'PID reciclado (StartTime distinto)' }
    }
    return [pscustomobject]@{ Vivo = $true; Verificado = $true; Motivo = 'vivo' }
}

function Get-Marcadores {
    $rutas = @()
    if (Test-Path -LiteralPath $MARCADOR_LOCAL) { $rutas += $MARCADOR_LOCAL }
    $dirs = @($REGISTRO_DIR)
    foreach ($x in $REGISTROS_EXTRA) { $dirs += (Join-Path $env:LOCALAPPDATA $x) }
    foreach ($d in $dirs) {
        if (Test-Path -LiteralPath $d) {
            $rutas += (Get-ChildItem -LiteralPath $d -Filter '*.json' -ErrorAction SilentlyContinue).FullName
        }
    }
    $vistos = @{}
    $out    = @()
    foreach ($r in ($rutas | Where-Object { $_ })) {
        # Un marcador ilegible es un marcador rancio: se trata igual, se limpia.
        $m = $null
        try { $m = Get-Content -LiteralPath $r -Raw -ErrorAction Stop | ConvertFrom-Json } catch { }
        if (-not $m -or -not $m.pid -or -not $m.arbol) {
            $out += [pscustomobject]@{ Archivo = $r; Marcador = $null; Ilegible = $true }
            continue
        }
        # El local y su copia en el registro son el MISMO marcador: no se cuenta dos veces.
        $clave = "$($m.pid)|$($m.inicio)"
        if ($vistos.ContainsKey($clave)) { continue }
        $vistos[$clave] = $true
        $out += [pscustomobject]@{ Archivo = $r; Marcador = $m; Ilegible = $false }
    }
    return $out
}

function Remove-Marcador([string]$archivo) {
    Remove-Item -LiteralPath $archivo -Force -ErrorAction SilentlyContinue
}

# --- 1. Este arbol ya tiene dueno? ------------------------------------------
# MEDIDO el 25-ago-2026: 'Get-Process -Name claude' devolvia 8 procesos y NINGUNO
# era un agente. Eran la app de ESCRITORIO (Claude.exe bajo WindowsApps; Electron
# levanta ~8) -- abierta a proposito para darle puente de disco al chat. O sea:
# el guard sonaba justo por hacer lo correcto. Una alarma que suena siempre se
# aprende a ignorar, y entonces deja de proteger.
#
# Se excluye SOLO lo que esta demostrado que no es un agente: la app, por su ruta.
# Todo lo demas -- incluido un proceso cuya ruta no se pueda leer -- sigue
# avisando. Este guard tiene que fallar CERRADO.

$RUTA_APP_ESCRITORIO = '*\WindowsApps\Claude_*\app\Claude.exe'

$procesos = @(Get-Process -Name claude -ErrorAction SilentlyContinue)
$app      = @($procesos | Where-Object { $_.Path -like    $RUTA_APP_ESCRITORIO })
$agentes  = @($procesos | Where-Object { $_.Path -notlike $RUTA_APP_ESCRITORIO })

if ($app.Count -gt 0) {
    Write-Host ""
    Write-Host "  [i] Ignorados $($app.Count) proceso(s) de la app de escritorio - no son agentes." -ForegroundColor DarkGray
}

# Ascendencia: esto NO necesita que nadie coopere. Win32_Process SI expone
# ParentProcessId (verificado el 25-ago). Agrupar por el ancestro comun dentro
# del propio conjunto de agentes convierte "3 extranos" en "1 listener con 2
# sesiones", que es una frase que si se puede leer a las 11 de la noche.
#
# OJO con quien es el "dueno": el marcador guarda el PID de ESTE PowerShell, y
# 'claude remote-control' es HIJO suyo (medido el 25-ago: listener PID 24784,
# padre 1328 = la ventana que lo lanzo). Asi que un marcador NO coincide con la
# raiz del grupo de agentes: coincide con su PADRE. Por eso se camina el arbol
# de procesos COMPLETO, no solo el subconjunto 'claude'.
$ppid = @{}
foreach ($w in @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)) {
    $ppid[[int]$w.ProcessId] = [int]$w.ParentProcessId
}
$idsAgente = @{}
foreach ($a in $agentes) { $idsAgente[[int]$a.Id] = $true }

# Raiz DENTRO del conjunto de agentes: sirve para agrupar en pantalla
# ("1 listener con 2 sesiones" en vez de "3 extranos").
function Get-RaizAgente([int]$id) {
    $actual = $id
    $saltos = 0
    while ($saltos -lt 32) {
        $padre = $ppid[$actual]
        if (-not $padre -or -not $idsAgente.ContainsKey($padre)) { return $actual }
        $actual = $padre
        $saltos++
    }
    return $actual
}

# Ancestria completa: sirve para decidir si un marcador EXPLICA un proceso.
function Test-Desciende([int]$id, [int]$ancestro) {
    $actual = $id
    $saltos = 0
    while ($saltos -lt 64) {
        if ($actual -eq $ancestro) { return $true }
        $padre = $ppid[$actual]
        if (-not $padre -or $padre -eq 0 -or $padre -eq $actual) { return $false }
        $actual = $padre
        $saltos++
    }
    return $false
}

# --- 2. Leer marcadores, limpiar los rancios --------------------------------
$marcadores = @(Get-Marcadores)
$vivos      = @()
$rancios    = @()

foreach ($e in $marcadores) {
    if ($e.Ilegible) {
        $rancios += [pscustomobject]@{ Archivo = $e.Archivo; Pid = '?'; Arbol = '[ilegible]'; Motivo = 'archivo ilegible o incompleto' }
        continue
    }
    $v = Test-MarcadorVivo $e.Marcador
    if ($v.Vivo) {
        $vivos += [pscustomobject]@{
            Archivo = $e.Archivo; Pid = [int]$e.Marcador.pid; Arbol = $e.Marcador.arbol
            Inicio  = $e.Marcador.inicio; Host = $e.Marcador.host; Verificado = $v.Verificado
        }
    } else {
        $rancios += [pscustomobject]@{ Archivo = $e.Archivo; Pid = $e.Marcador.pid; Arbol = $e.Marcador.arbol; Motivo = $v.Motivo }
    }
}

# El caso RANCIO es obligatorio: sin el, matar un remoto a lo bruto (que es
# justo lo que paso hoy) deja el arbol bloqueado para siempre, y eso es peor
# que el ruido que este arreglo viene a quitar.
if ($rancios.Count -gt 0) {
    Write-Host ""
    foreach ($r in $rancios) {
        Write-Host "  [i] Marcador rancio: PID $($r.Pid) - $($r.Motivo). Se limpia y se sigue." -ForegroundColor DarkGray
        Write-Host "      $($r.Archivo)" -ForegroundColor DarkGray
        Remove-Marcador $r.Archivo
    }
}

# --- 3. Los cuatro desenlaces -----------------------------------------------
$mismoArbol = @($vivos | Where-Object { $_.Arbol.TrimEnd('\').ToLowerInvariant() -eq $ARBOL.TrimEnd('\').ToLowerInvariant() })
$otroArbol  = @($vivos | Where-Object { $_.Arbol.TrimEnd('\').ToLowerInvariant() -ne $ARBOL.TrimEnd('\').ToLowerInvariant() -and $_.Verificado })

# (a) Marcador vivo de ESTE arbol -> se para, y se dice COMO SALIR. Un candado
#     que no explica como abrirse acaba desactivado por quien lo encuentra.
if ($mismoArbol.Count -gt 0) {
    $m = $mismoArbol[0]
    Write-Host ""
    Write-Host "  [X] Este arbol YA tiene un control remoto activo." -ForegroundColor Red
    Write-Host "      PID $($m.Pid), arrancado $($m.Inicio) en $($m.Host)" -ForegroundColor Red
    Write-Host "      Arbol: $($m.Arbol)" -ForegroundColor Red
    Write-Host ""
    Write-Host "      COMO SALIR - una de estas dos:" -ForegroundColor Yellow
    Write-Host "       1. Usa el que ya esta corriendo (es el mismo repo: no hace falta otro)." -ForegroundColor Yellow
    Write-Host "       2. Cierra esa ventana con Ctrl+C y vuelve a correr esto." -ForegroundColor Yellow
    Write-Host "          Si esa ventana ya no existe, el marcador es rancio y se limpia solo" -ForegroundColor Yellow
    Write-Host "          en la siguiente corrida." -ForegroundColor Yellow
    exit 1
}

# (b) Procesos explicados por un marcador vivo de OTRO arbol -> se informa y NO
#     se pregunta. Este es el caso que hoy costaba una sesion.
$explicados = @{}
foreach ($m in $otroArbol) {
    foreach ($a in $agentes) {
        if (Test-Desciende ([int]$a.Id) ([int]$m.Pid)) { $explicados[[int]$a.Id] = $m }
    }
}
if ($otroArbol.Count -gt 0) {
    Write-Host ""
    foreach ($m in $otroArbol) {
        $mios = @($explicados.GetEnumerator() | Where-Object { $_.Value.Pid -eq $m.Pid })
        Write-Host "  [i] Control remoto de OTRO ambito, conocido - no se pisan." -ForegroundColor DarkGray
        Write-Host "      Ambito: $($m.Arbol)" -ForegroundColor DarkGray
        Write-Host "      PID $($m.Pid) desde $($m.Inicio) - explica $($mios.Count) proceso(s) mas." -ForegroundColor DarkGray
    }
}

# (c) Lo que NADIE reclama -> se pregunta, igual que hoy. Lista blanca, no lista
#     negra: lo no explicado NO se deja pasar en silencio.
$huerfanos = @($agentes | Where-Object { -not $explicados.ContainsKey([int]$_.Id) })

# La senal que si mide ESTE arbol, no la maquina entera.
$lock = Test-Path -LiteralPath (Join-Path $ARBOL '.git\index.lock')
if ($lock) {
    Write-Host ""
    Write-Host "  [!] Hay un .git\index.lock: algo esta a media operacion de git en este arbol." -ForegroundColor Red
}

if ($huerfanos.Count -gt 0 -or $lock) {
    Write-Host ""
    if ($huerfanos.Count -gt 0) {
        $grupos = $huerfanos | Group-Object { Get-RaizAgente ([int]$_.Id) }
        Write-Host "  [!] $($huerfanos.Count) proceso(s) 'claude' que nadie reclama, en $($grupos.Count) grupo(s):" -ForegroundColor Yellow
        foreach ($g in $grupos) {
            Write-Host "      - grupo de PID $($g.Name) ($($g.Count) proceso(s)):" -ForegroundColor Yellow
            foreach ($p in $g.Group) {
                $ruta = if ($p.Path) { $p.Path } else { '[ruta no legible - se avisa por si acaso]' }
                Write-Host "          PID $($p.Id)  $ruta" -ForegroundColor Yellow
            }
        }
        Write-Host "      Si trabajan sobre OTRO arbol, esta bien: arboles distintos no se pisan." -ForegroundColor Yellow
        Write-Host "      Si alguno trabaja sobre ESTE repo, NO continues: en spawn mode same-dir" -ForegroundColor Yellow
        Write-Host "      dos agentes comparten el arbol y se pisan." -ForegroundColor Yellow
        Write-Host "      (No lo reclama ningun marcador: o es un remoto viejo sin marcador, o" -ForegroundColor DarkGray
        Write-Host "       lo lanzo alguien a mano.)" -ForegroundColor DarkGray
    }
    if ($SoloDiagnostico) {
        Write-Host "      [diagnostico] aqui se preguntaria: Continuar de todos modos? (s/N)" -ForegroundColor Magenta
    } else {
        $r = Read-Host "      Continuar de todos modos? (s/N)"
        if ($r -ne 's' -and $r -ne 'S') { Write-Host "  Cancelado." -ForegroundColor DarkGray; exit 1 }
    }
} elseif ($otroArbol.Count -eq 0) {
    Write-Host ""
    Write-Host "  [ok] Nadie mas sobre este arbol." -ForegroundColor Green
}

# --- 4. Estado del arbol que heredaran las sesiones -------------------------
$rama  = (git rev-parse --abbrev-ref HEAD 2>$null)
$sha   = (git rev-parse --short HEAD 2>$null)
$sucio = git status --porcelain 2>$null

Write-Host ""
if ($rama) { Write-Host "  Rama : $rama ($sha)" }
else       { Write-Host "  Rama : [no se pudo leer git desde aqui]" -ForegroundColor Yellow }

if ($sucio) {
    $n = ($sucio | Measure-Object).Count
    Write-Host "  Arbol: $n archivo(s) sin commitear" -ForegroundColor Yellow
    Write-Host "         Las sesiones remotas arrancan sobre este estado." -ForegroundColor DarkGray
    $sucio | Select-Object -First 10 | ForEach-Object { Write-Host "         $_" -ForegroundColor DarkGray }
    if ($n -gt 10) { Write-Host "         ... y $($n - 10) mas" -ForegroundColor DarkGray }
} else {
    Write-Host "  Arbol: limpio" -ForegroundColor Green
}

# El mismo estado que vera el implementador con -Estado, para quien lanza.
Write-Host ""
Show-Estado | ForEach-Object { Write-Host ("  " + $_) -ForegroundColor DarkGray }

if ($SoloDiagnostico) {
    Write-Host ""
    Write-Host "  [diagnostico] veredicto: SE PODRIA ARRANCAR. No se lanza nada." -ForegroundColor Magenta
    Write-Host ""
    exit 0
}

# --- 5. Lo que el script NO puede comprobar por ti --------------------------
Write-Host ""
Write-Host "  Antes de irte, a mano:" -ForegroundColor DarkGray
Write-Host "   - laptop enchufada y con la suspension desactivada (por energia Y por tapa)" -ForegroundColor DarkGray
Write-Host "   - no abrir Claude Code en la terminal de VS Code mientras esto corra" -ForegroundColor DarkGray
Write-Host "   - deja ESTA ventana abierta (minimizada esta bien). Ctrl+C la detiene." -ForegroundColor DarkGray
Write-Host ""

# --- 6. Declarar el arbol y arrancar ----------------------------------------
# El marcador se escribe ANTES de lanzar y se borra en el finally, para que
# Ctrl+C tambien limpie. Vive en .git\ a proposito: git nunca lo mira, asi que
# no puede aparecer en 'git status' ni colarse en un commit.
$marcador = [pscustomobject]@{
    pid    = $PID
    arbol  = $ARBOL
    inicio = (Get-Process -Id $PID).StartTime.ToString('o')
    host   = $env:COMPUTERNAME
}
$copiaRegistro = Join-Path $REGISTRO_DIR ("{0}.json" -f (Get-HashArbol $ARBOL))

try {
    $json = $marcador | ConvertTo-Json -Compress
    Set-Content -LiteralPath $MARCADOR_LOCAL -Value $json -Encoding utf8
    if (-not (Test-Path -LiteralPath $REGISTRO_DIR)) {
        New-Item -ItemType Directory -Path $REGISTRO_DIR -Force | Out-Null
    }
    Set-Content -LiteralPath $copiaRegistro -Value $json -Encoding utf8

    claude remote-control --spawn=same-dir
}
finally {
    Remove-Marcador $MARCADOR_LOCAL
    Remove-Marcador $copiaRegistro
}
