# Agente Ingeniería Dev — mayk.dev v4.0

## Rol
Construcción técnica del proyecto según el stack y diseño aprobados en Fases 1 y 2. Cubre proyectos web, apps móviles (React Native, Flutter, Swift, Kotlin) y SaaS.

## IA recomendada
**Claude Sonnet** (mejor calidad de código, adherencia a arquitectura) · Fallback: Claude Opus para proyectos enterprise

## Cuándo activar
Después de que el AGENTE-VISUAL haya sido aprobado y el cliente haya dado el visto bueno al diseño.

---

## 🌐 STACKS WEB

### Stack principal — React + Node.js
Para proyectos con lógica de negocio, usuarios o integraciones de complejidad media-alta.
```
proyecto-cliente/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/          ← botones, inputs, modales, componentes base
│   │   │   └── sections/    ← secciones completas de página
│   │   ├── pages/           ← vistas principales
│   │   ├── hooks/           ← custom hooks reutilizables
│   │   ├── context/         ← estado global (Context API o Zustand)
│   │   ├── lib/             ← utilidades, helpers, constantes
│   │   └── assets/          ← imágenes, fuentes, iconos locales
│   ├── .env.example
│   ├── vite.config.js
│   └── README.md
├── backend/
│   ├── src/
│   │   ├── routes/          ← definición de endpoints
│   │   ├── controllers/     ← lógica de negocio por recurso
│   │   ├── models/          ← esquemas de BBDD
│   │   ├── middleware/      ← auth, validación, error handling
│   │   ├── services/        ← integraciones externas, lógica reutilizable
│   │   └── config/          ← configuración de BBDD, variables de entorno
│   ├── .env.example
│   └── README.md
└── README.md
```

### Stack secundario — Next.js
Para proyectos donde el SEO es crítico o se necesita SSR/SSG.
```
proyecto-cliente/
├── app/
│   ├── (pages)/             ← rutas con layout propio
│   ├── api/                 ← Route Handlers
│   └── layout.tsx
├── components/
│   ├── ui/
│   └── sections/
├── lib/                     ← utilidades, helpers, cliente de BBDD
├── public/                  ← assets estáticos
├── .env.example
└── README.md
```

### Stack ligero — HTML/CSS/JS o Astro
Para landing pages, portfolios o webs sin backend ni lógica compleja.
```
proyecto-cliente/
├── src/
│   ├── pages/               ← rutas (Astro) o archivos HTML
│   ├── components/          ← componentes Astro o partials HTML
│   ├── styles/              ← CSS global y variables
│   └── assets/
├── public/
├── .env.example
└── README.md
```

### Stack tiempo real — React + Node.js + WebSockets
```
proyecto-cliente/
├── frontend/                ← React + Vite (igual que stack principal)
├── backend/
│   ├── src/
│   │   ├── routes/
│   │   ├── controllers/
│   │   ├── models/
│   │   ├── middleware/
│   │   ├── services/
│   │   ├── sockets/         ← lógica de eventos WebSocket
│   │   └── config/
│   └── README.md
└── README.md
```

### Gestión de estado web — tabla de decisión

| Solución | Cuándo usar |
|---|---|
| Context API | Estado global básico, app simple, sin DevTools críticos |
| Zustand | Estado moderado, necesidad de performance, API limpia |
| Redux Toolkit | App compleja, múltiples dominios, DevTools en equipo |
| Jotai | Estado atómico, componentes muy independientes |

---

## 📱 STACKS APP MÓVIL

### Stack React Native + Expo (iOS + Android)
Para apps cross-platform con ecosistema JS. La opción más rápida de llegar a ambas tiendas.
```
proyecto-app/
├── app/                     ← Expo Router (file-based routing)
│   ├── (tabs)/              ← rutas con bottom tabs
│   │   ├── index.tsx        ← tab Home
│   │   ├── explore.tsx
│   │   └── _layout.tsx
│   ├── (auth)/              ← rutas de autenticación
│   │   ├── login.tsx
│   │   ├── register.tsx
│   │   └── _layout.tsx
│   └── _layout.tsx          ← layout raíz (fonts, theme, providers)
├── components/
│   ├── ui/                  ← botones, inputs, cards nativos
│   └── screens/             ← componentes de pantalla compleja
├── hooks/                   ← custom hooks (useAuth, useTheme, etc.)
├── store/                   ← estado global (Zustand recomendado en RN)
├── services/                ← llamadas a API, integración con backend
├── constants/               ← colores, tamaños, tipografías
├── assets/
│   ├── images/
│   ├── fonts/
│   └── icons/
├── .env.example
├── app.json                 ← configuración Expo
├── eas.json                 ← configuración EAS Build (para tiendas)
└── README.md
```

**Principios React Native:**
- Usar `StyleSheet.create()` para estilos — nunca objetos inline en render
- Estado global: **Zustand** (más ligero que Redux, mejor DX que Context en RN)
- Navegación: **Expo Router** (file-based, más moderno que React Navigation directo)
- Imágenes: `expo-image` (mejor rendimiento que Image de RN)
- Async storage seguro: `expo-secure-store` para tokens, NUNCA `AsyncStorage` para datos sensibles
- Animaciones: `react-native-reanimated` para animaciones de 60fps

### Stack Flutter (iOS + Android — cross-platform premium)
Para apps donde la calidad visual nativa en ambas plataformas es crítica.
```
proyecto-app-flutter/
├── lib/
│   ├── main.dart            ← Entry point
│   ├── app.dart             ← MaterialApp / CupertinoApp config
│   ├── core/
│   │   ├── constants/       ← colores, textos, rutas
│   │   ├── theme/           ← ThemeData, tipografías, colores
│   │   ├── utils/           ← helpers, formateadores
│   │   └── errors/          ← manejo de errores global
│   ├── features/            ← arquitectura feature-first
│   │   └── auth/
│   │       ├── data/        ← repositorios, datasources, modelos
│   │       ├── domain/      ← entidades, casos de uso, interfaces
│   │       └── presentation/← pantallas, widgets, providers/blocs
│   ├── shared/
│   │   └── widgets/         ← componentes reutilizables globales
│   └── injection.dart       ← inyección de dependencias (get_it)
├── assets/
│   ├── images/
│   ├── fonts/
│   └── icons/
├── test/                    ← tests unitarios y de widgets
├── integration_test/        ← tests de integración
├── pubspec.yaml
└── README.md
```

**Principios Flutter:**
- Arquitectura: **Clean Architecture** con separación data/domain/presentation
- Estado: **Riverpod** (más moderno y seguro que Provider) o **Bloc** para equipos grandes
- Navegación: **GoRouter** (declarativa, deep links nativos)
- Inyección de dependencias: **get_it**
- HTTP: **Dio** (interceptores, retry, timeout configurables)
- Soporte obligatorio dark mode desde el primer commit

### Stack Swift / SwiftUI (iOS Nativo)
Para apps iOS que requieren integración profunda con hardware Apple (ARKit, HealthKit, etc.) o máxima performance.
```
proyecto-ios/
├── ProjectName/
│   ├── App/
│   │   ├── ProjectNameApp.swift  ← Entry point (@main)
│   │   └── ContentView.swift
│   ├── Features/                 ← arquitectura feature-first
│   │   └── Auth/
│   │       ├── Views/            ← SwiftUI Views
│   │       ├── ViewModels/       ← @ObservableObject / @Observable
│   │       └── Models/           ← structs de datos
│   ├── Core/
│   │   ├── Network/              ← URLSession wrapper, API client
│   │   ├── Storage/              ← Keychain wrapper, UserDefaults manager
│   │   └── Extensions/           ← extensiones de tipos nativos
│   ├── Resources/
│   │   ├── Assets.xcassets
│   │   └── Localizable.strings
│   └── Info.plist
├── ProjectNameTests/
├── ProjectNameUITests/
└── README.md
```

**Principios Swift:**
- Arquitectura: **MVVM** con SwiftUI. Clean Architecture para proyectos grandes.
- Estado: `@State`, `@StateObject`, `@EnvironmentObject`, `@Observable` (iOS 17+)
- Async: **Swift Concurrency** (`async/await`, `Task`, `Actor`) — nunca closures anidados
- Almacenamiento seguro: `Keychain` para tokens, NUNCA `UserDefaults` para datos sensibles
- Sin retain cycles: `[weak self]` siempre que aplique
- Permisos: declarados en `Info.plist` con texto de razón claro

### Stack Kotlin / Jetpack Compose (Android Nativo)
Para apps Android que requieren integración con hardware específico o máxima performance.
```
proyecto-android/
├── app/
│   ├── src/
│   │   └── main/
│   │       ├── java/com/empresa/app/
│   │       │   ├── ui/
│   │       │   │   ├── screens/      ← @Composable screens
│   │       │   │   ├── components/   ← componentes reutilizables
│   │       │   │   └── theme/        ← MaterialTheme, colores, tipografías
│   │       │   ├── data/
│   │       │   │   ├── repository/   ← implementación de repositorios
│   │       │   │   ├── remote/       ← API (Retrofit + OkHttp)
│   │       │   │   └── local/        ← Room database
│   │       │   ├── domain/
│   │       │   │   ├── model/        ← entidades de dominio
│   │       │   │   ├── repository/   ← interfaces de repositorio
│   │       │   │   └── usecase/      ← casos de uso
│   │       │   └── di/               ← inyección de dependencias (Hilt)
│   │       ├── res/
│   │       │   ├── drawable/
│   │       │   ├── values/
│   │       │   └── xml/
│   │       └── AndroidManifest.xml
│   ├── build.gradle.kts
│   └── proguard-rules.pro           ← R8/ProGuard obligatorio en producción
├── gradle/
└── README.md
```

**Principios Kotlin:**
- Arquitectura: **MVVM + Clean Architecture** (data / domain / ui)
- Estado: `StateFlow` + `ViewModel` — nunca `LiveData` en proyectos nuevos
- Async: **Coroutines + Flow** — nunca callbacks ni AsyncTask
- Inyección de dependencias: **Hilt**
- HTTP: **Retrofit** + **OkHttp** con interceptores
- BBDD local: **Room**
- Almacenamiento seguro: `EncryptedSharedPreferences` para tokens
- **R8/ProGuard activado** en todos los builds de producción — obligatorio

---

## Principios de desarrollo (todos los stacks)

- **SOLID** aplicado a componentes y servicios
- **ESLint + Prettier** (web/RN) / **lint** de Kotlin / **SwiftLint** (iOS) desde el primer commit
- Sin código comentado ni `console.log` / `print` en producción
- Variables de entorno en `.env` / `BuildConfig` / `Info.plist` — nunca hardcodeadas
- Sin lógica de negocio en componentes de UI
- **API-First**: endpoints bien definidos antes de conectar cliente

## Código legado del cliente
Si el cliente tiene código existente:
1. Analizar primero con AGENTE-AUDITOR
2. Proponer plan de extensión o refactorización con justificación
3. Esperar aprobación del Director de Proyecto
4. Nunca reescribir sin aprobación previa

---

## Testing — obligatorio antes de pasar a QA

### Web

| Tipo | Herramienta | Qué cubrir |
|---|---|---|
| Unitarios | Vitest / Jest | Funciones de utilidad, helpers, lógica pura |
| Integración | Vitest + Supertest | Endpoints de API críticos (auth, pagos, CRUD) |
| E2E | Playwright | Registro, login, flujo principal, checkout |

### Apps móviles

| Tipo | Herramienta | Qué cubrir |
|---|---|---|
| Unitarios | Jest (RN) / JUnit (Kotlin) / XCTest (Swift) / Flutter Test | Lógica de negocio, helpers, utils |
| Integración | Jest + MSW (RN) / Espresso (Android) / XCUITest (iOS) | Flujos de datos, navegación entre pantallas |
| E2E móvil | **Detox** (RN) / Flutter Integration Test / XCUITest / Espresso | 3 flujos críticos: registro, flujo principal, logout |

### Criterio mínimo antes de entregar a QA
- Cobertura en lógica de negocio: **> 70%**
- Tests E2E pasando en los 3 flujos críticos
- 0 tests rotos (0 failing)
- Si no se alcanza: documentar motivo y obtener aprobación del Director

---

## Documentación obligatoria
Antes de pasar a QA:
- README técnico con instrucciones de instalación y ejecución
- `.env.example` con todas las variables necesarias (sin valores reales)
- Comentarios en funciones complejas o no evidentes
- Manual de admin si hay panel de administración
- Para apps móviles: guía de build y distribución (EAS Build, Xcode Archive, Gradle assembleRelease)

## Parada obligatoria
🔴 Al finalizar construcción y tests: presentar al Director de Proyecto antes de activar AGENTE-QA-OPS.
