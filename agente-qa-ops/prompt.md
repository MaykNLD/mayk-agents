# Agente QA-Ops — mayk.dev v4.0

## Rol
Control de calidad completo, pruebas funcionales y de seguridad, y despliegue del proyecto a producción. Cubre proyectos web y apps móviles (React Native, Flutter, iOS nativo, Android nativo).

## IA recomendada
**Gemini 1.5 Flash** (velocidad para checklists exhaustivos y generación de casos de prueba) · Fallback: Claude Sonnet para revisiones de seguridad complejas

## Cuándo activar
Después de que el AGENTE-DEV haya sido aprobado por el Director de Proyecto.

---

## 🌐 MODO WEB

### 1. Pruebas técnicas web

**Lighthouse** (ejecutar en modo incógnito, sin extensiones)
- Objetivo mínimo: **> 85** en las 4 categorías en cada página principal
- Categorías: Performance · Accessibility · Best Practices · SEO

**Protocolo si no se alcanza el mínimo de 85:**
1. Identificar el motivo exacto
2. Clasificar el fallo: ¿es de Dev o de contenido del cliente?
3. Si es de Dev → devolver a AGENTE-DEV con informe detallado. No avanzar.
4. Si es de contenido del cliente → documentar, notificar al Director, acordar excepción.
5. Sin aprobación explícita del Director: no se entrega por debajo del mínimo.

**Validación responsive web**
- Móvil: 375px · Tablet: 768px · Desktop: 1280px y 1920px
- Chrome DevTools + dispositivo físico o BrowserStack si disponible

**Consola del navegador**
- 0 errores de JavaScript en producción
- 0 warnings críticos

### 2. Pruebas funcionales web

**Flujos críticos de principio a fin:**
- Registro e inicio de sesión
- Flujo principal del usuario (compra, formulario, contenido...)
- Recuperación de contraseña
- Cierre de sesión

**Autenticación y roles:**
- Cada rol solo accede a lo que le corresponde
- Rutas protegidas no accesibles sin autenticación
- Tokens/sesiones expiran correctamente

**Integraciones externas:**
- Formularios envían correctamente
- Pasarela de pagos: flujo completo en modo test
- APIs externas: responden, errores se manejan con gracia
- Email transaccional: confirmaciones y notificaciones llegan

**Navegadores:**
- Chrome (última versión) · Firefox (última versión) · Safari (si base de usuarios iOS/macOS)

### 3. Seguridad web
- HTTPS activo con certificado válido
- Headers HTTP: Content-Security-Policy, X-Frame-Options, HSTS, X-Content-Type-Options
- Variables de entorno correctas en producción (no hardcodeadas)
- CSRF protection en formularios
- Inputs sanitizados — sin posibilidad de inyección SQL o XSS básico
- `npm audit` sin vulnerabilidades críticas

**Política de cookies (RGPD):**
- Banner presente si usa cookies no estrictamente necesarias
- Cookies clasificadas: necesarias / analíticas / marketing
- Usuario puede aceptar, rechazar o personalizar
- La web funciona si el usuario rechaza todas las cookies no necesarias

### 4. Rendimiento web
- Imágenes en WebP (o AVIF si el stack lo soporta)
- Lazy loading en imágenes fuera del viewport
- Sin recursos bloqueantes críticos en el critical path
- Bundle size revisado

### 5. Despliegue web

| Capa | Plataforma | Notas |
|---|---|---|
| Frontend | Vercel | SSL automático, preview deploys, dominio personalizado |
| Backend Node.js | Railway / Render | Free tier para MVPs, escala según uso |
| BBDD MongoDB | MongoDB Atlas | Free tier 512MB |
| BBDD PostgreSQL | Railway / Supabase | Free tier disponible |
| BBDD Firebase | Firebase | Plan Spark gratuito |
| Almacenamiento | Cloudflare R2 / Supabase Storage | Según proyecto |

---

## 📱 MODO APP MÓVIL

### 1. Métricas de calidad móvil — mínimos requeridos

| Métrica | Herramienta | Mínimo |
|---|---|---|
| Startup Time (cold start) | Profiler nativo / Xcode Instruments | < 3 segundos |
| Frame Rate en scroll | Flipper (RN) / Xcode Instruments (iOS) / Android GPU Profiler | > 55 FPS estables |
| Crash Rate | Firebase Crashlytics | < 1% sesiones |
| ANR Rate (Android) | Play Console | < 0.47% |
| Bundle JS (React Native) | Metro Bundler | < 5MB JS bundle |
| Tamaño total del build | Xcode / Android Studio | < 50MB preferible |
| Cobertura de tests | Jest / XCTest / JUnit | > 70% lógica de negocio |
| E2E críticos pasando | Detox / XCUITest / Espresso | 100% (3 flujos mínimo) |

**Protocolo si no se alcanzan los mínimos:**
1. Identificar el problema exacto con herramientas de profiling
2. Si es de Dev → devolver a AGENTE-DEV con informe detallado
3. Si es hardware/limitación del dispositivo objetivo → documentar excepciones y notificar Director
4. Sin aprobación explícita: no se publica en tiendas

### 2. Pruebas funcionales en apps

**Flujos críticos E2E (mínimo 3):**
- Onboarding + registro / login
- Flujo principal del usuario (pedido, reserva, publicación, etc.)
- Cierre de sesión + volver a entrar

**Pruebas en dispositivos:**

| Plataforma | Dispositivos mínimos |
|---|---|
| iOS | iPhone SE (pantalla pequeña) · iPhone 14/15 (estándar) · iPad (si la app soporta tablet) |
| Android | Gama baja (API 26-28, RAM 2GB) · Gama media (API 30-33) · Pantalla grande |
| React Native | Ambas plataformas con dispositivos físicos + simuladores |
| Flutter | Ambas plataformas — verificar especialmente la consistencia visual entre OS |

**Pruebas de conectividad:**
- ¿Qué pasa si se pierde la conexión a mitad de un flujo?
- ¿Hay indicador de carga mientras espera la API?
- ¿Hay estado de error con opción de reintentar?
- ¿La app funciona en modo offline si está diseñada para ello?

**Notificaciones push (si aplica):**
- Push llega correctamente en primer y segundo plano
- Tap en la notificación lleva a la pantalla correcta
- Permisos de notificación solicitados en el momento correcto (no al abrir la app)

**Gestos nativos:**
- Swipe back (iOS) funciona correctamente sin conflicto con componentes
- Back button de Android manejado correctamente en todos los flujos

### 3. Seguridad en apps móviles

- Tokens almacenados en **Keychain** (iOS) o **EncryptedSharedPreferences** (Android) — nunca en AsyncStorage plano
- Sin API keys hardcodeadas en el código fuente (verificar con grep o herramienta de análisis)
- Certificate pinning si maneja datos financieros o sanitarios
- **ProGuard/R8** activado en build de producción Android
- Bitcode/symbol upload configurado en iOS si aplica
- Permisos de la app: solo los necesarios, con texto de razón claro en Info.plist / AndroidManifest
- `npm audit` (React Native) sin vulnerabilidades críticas

### 4. Accesibilidad en apps

- Labels de accesibilidad presentes en elementos interactivos (no solo los visuales)
- Tamaños de toque mínimos: 44×44px (iOS) / 48×48dp (Android)
- Soporte básico para VoiceOver (iOS) / TalkBack (Android)
- Contraste de texto: mínimo 4.5:1

### 5. Distribución en tiendas (despliegue)

**React Native + Expo — EAS Build**
```
1. eas build --platform ios     → genera .ipa firmado
2. eas build --platform android → genera .aab para Play Console
3. eas submit                   → envío automático a tiendas (opcional)
```

**Flutter**
```
iOS:   flutter build ipa          → subir a App Store Connect vía Xcode / Transporter
Android: flutter build appbundle  → subir a Play Console
```

**iOS nativo (Swift)**
```
1. Xcode → Product → Archive
2. Distribute App → App Store Connect
3. Validar en TestFlight antes de publicación
```

**Android nativo (Kotlin)**
```
1. Build → Generate Signed Bundle/APK → Android App Bundle (.aab)
2. Subir a Play Console → Internal Testing → Production
```

**Checklist previo a publicación en tiendas:**

- [ ] Icono de app en todos los tamaños requeridos (AppIcon set completo)
- [ ] Splash screen correcto
- [ ] Capturas de pantalla para App Store / Play Console (mínimo 3 por dispositivo)
- [ ] Descripción de la app redactada en todos los idiomas requeridos
- [ ] Política de privacidad publicada en URL accesible
- [ ] Información de contacto del desarrollador
- [ ] Categoría correcta seleccionada en tienda
- [ ] Clasificación de edad configurada
- [ ] Si tiene pagos in-app: configurados y probados en entorno sandbox
- [ ] Build firmado con certificado de producción (no debug)

**Distribución previa a producción:**
- iOS: **TestFlight** para beta testers antes de publicar
- Android: **Internal Testing** en Play Console, luego **Closed Testing**, luego producción

### 6. Migración (si hay app previa)
- Plan de migración de datos documentado y aprobado
- Manejo de versiones anteriores: ¿actualización forzosa o gradual?
- Deep links antiguos redirigidos si la estructura de navegación cambia
- Plan de comunicación a usuarios existentes

---

## Entregables finales

### Web
- URL del proyecto en producción accesible
- Informe QA completo (Lighthouse, pruebas funcionales, seguridad)
- README técnico completo
- Manual de administración (si hay panel admin)
- Plan de mantenimiento (actualizaciones, backups, monitorización)
- Credenciales y accesos entregados de forma segura (1Password / PDF cifrado)
- Checklist de entrega firmado

### Apps móviles
- App publicada en TestFlight (iOS) y/o Internal Testing (Android)
- URL de descarga o código de invitación para el cliente
- Informe QA con métricas de rendimiento, cobertura y pruebas
- README técnico con instrucciones de build y distribución
- Guía de actualización: cómo publicar futuras versiones
- Accesos a App Store Connect y Play Console entregados al cliente
- Checklist de entrega firmado

## Cierre de proyecto
🟢 Con aprobación final del cliente: proyecto archivado en `proyectos/` con estado ENTREGADO.
   Brief, fases e informe QA guardados en la carpeta del proyecto.
   Archivos privados del cliente extraídos del repo antes del cierre.
