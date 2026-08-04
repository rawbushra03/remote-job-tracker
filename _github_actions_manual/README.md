# ⚙️ Activar la actualización automática diaria (GitHub Actions)

El workflow que actualiza los empleos cada 24 h está listo en este mismo
folder: **`update-jobs.yml`**.

> ¿Por qué está aquí y no en `.github/workflows/`?
> El token con el que se subió el código no tenía el permiso especial
> `workflows` de GitHub, así que GitHub rechaza subir archivos dentro de
> `.github/workflows/`. Tú SÍ tienes ese permiso desde tu cuenta, así que
> puedes agregarlo en 1 minuto. Aquí van las 2 formas de hacerlo.

---

## ✅ Opción A — Desde la web de GitHub (la más fácil, sin comandos)

1. Entra a tu repo: <https://github.com/rawbushra03/remote-job-tracker>
2. Asegúrate de estar en la rama `arena/019fcb6c-remote-job-tracker`
   (o primero haz merge a `main` — ver más abajo).
3. Haz clic en **Add file → Create new file**.
4. En el nombre del archivo escribe exactamente:

   ```
   .github/workflows/update-jobs.yml
   ```

   (GitHub creará las carpetas automáticamente al escribir las `/`).
5. Abre el archivo `_github_actions_manual/update-jobs.yml` de este repo,
   **copia TODO su contenido** y pégalo en el editor.
6. Abajo, clic en **Commit new file**.
7. Ve a la pestaña **Actions** del repo → verás el workflow
   *"Update remote jobs daily"*. Haz clic en **Run workflow** para probarlo
   ahora mismo (no tienes que esperar 24 h).

---

## ✅ Opción B — Desde tu PC (PowerShell)

Desde tu propia máquina tu usuario sí tiene permiso `workflows`:

```powershell
cd C:\Users\Admin\MisProyectos\remote-job-tracker

# Trae la rama que ya subimos
git fetch origin
git checkout arena/019fcb6c-remote-job-tracker

# Crea la carpeta y copia el workflow a su lugar definitivo
New-Item -ItemType Directory -Force -Path .github\workflows
Copy-Item _github_actions_manual\update-jobs.yml .github\workflows\update-jobs.yml

git add .github/workflows/update-jobs.yml
git commit -m "ci: enable daily auto-update workflow"
git push origin arena/019fcb6c-remote-job-tracker
```

Luego ve a la pestaña **Actions** en GitHub y ejecuta *Run workflow* para
probarlo.

---

## 🔎 ¿Qué hace el workflow?

- Se ejecuta **todos los días a las 06:00 UTC** (~01:00 EST) y también
  cuando lo lanzas a mano (*workflow_dispatch*).
- Instala las dependencias, corre `python src/aggregate.py --sample --max-jobs 500`
  (trae empleos de las 4 fuentes), regenera los gráficos, y hace **commit + push**
  del `data/jobs_sample.csv` actualizado.
- Streamlit Cloud detecta el commit y **redeploya el dashboard solo**.
- **No requiere ningún secret ni API key** — todas las fuentes son públicas y
  usa el `GITHUB_TOKEN` que GitHub provee automáticamente.

> 💡 Recuerda: para que el workflow pueda hacer push, el repo debe permitir
> escritura a Actions. Ve a **Settings → Actions → General → Workflow
> permissions** y marca **"Read and write permissions"** (suele venir así por
> defecto en repos personales).
