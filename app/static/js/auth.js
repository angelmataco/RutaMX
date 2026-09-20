// Registro/login (nombre + apellido + PIN de 4 dígitos, sin correo) y
// estado de sesión, compartido con main.js a través de window.RutaAuth.

const RutaAuth = (() => {
  let usuarioActual = null;
  let promesaListo = null;
  const listenersLogin = [];
  const listenersLogout = [];

  const elementos = {};

  function cachearElementos() {
    elementos.modal = document.querySelector("[data-modal-auth]");
    elementos.widget = document.querySelector("[data-auth-widget]");
    elementos.abrirLoginBtn = document.querySelector("[data-abrir-login]");
    elementos.cerrarSesionBtn = document.querySelector("[data-cerrar-sesion]");
    elementos.usuarioInfo = document.querySelector("[data-usuario-info]");
    elementos.usuarioNombre = document.querySelector("[data-usuario-nombre]");
    elementos.avatarBtn = document.querySelector("[data-avatar-btn]");
    elementos.avatarImg = document.querySelector("[data-avatar-img]");
    elementos.avatarMenu = document.querySelector("[data-avatar-menu]");
    elementos.menuUsuario = document.querySelector("[data-menu-usuario]");
    elementos.vistaLogin = document.querySelector("[data-vista-login]");
    elementos.vistaRegistro = document.querySelector("[data-vista-registro]");
    elementos.formLogin = document.querySelector("[data-form-login]");
    elementos.formRegistro = document.querySelector("[data-form-registro]");
    elementos.errorLogin = document.querySelector("[data-error-login]");
    elementos.errorRegistro = document.querySelector("[data-error-registro]");
    elementos.irARegistro = document.querySelector("[data-ir-a-registro]");
    elementos.irALogin = document.querySelector("[data-ir-a-login]");
  }

  function renderNavbar() {
    if (!elementos.widget) return;
    elementos.abrirLoginBtn.hidden = Boolean(usuarioActual);
    elementos.usuarioInfo.hidden = !usuarioActual;
    if (usuarioActual) {
      elementos.usuarioNombre.textContent = `${usuarioActual.nombre} ${usuarioActual.apellido}`;
      pintarAvatar(`${usuarioActual.nombre} ${usuarioActual.apellido}`);
    } else {
      alternarMenu(false);
      RutaAvatar.detener();
    }
  }

  // El avatar (Blobatar) vive en avatar.js.
  function pintarAvatar(texto) {
    RutaAvatar.pintar(texto, elementos.avatarImg, elementos.avatarMenu, elementos.widget.dataset.blobatarDir);
  }

  function alternarMenu(abrir) {
    if (!elementos.menuUsuario) return;
    const abierto = typeof abrir === "boolean" ? abrir : elementos.menuUsuario.hidden;
    elementos.menuUsuario.hidden = !abierto;
    elementos.avatarBtn.setAttribute("aria-expanded", String(abierto));
    RutaAvatar.menu(abierto);
  }

  function mostrarVista(vista) {
    const esLogin = vista === "login";
    elementos.vistaLogin.hidden = !esLogin;
    elementos.vistaRegistro.hidden = esLogin;
    elementos.errorLogin.hidden = true;
    elementos.errorRegistro.hidden = true;
  }

  function abrirModal(vista = "login") {
    mostrarVista(vista);
    if (elementos.modal && typeof elementos.modal.showModal === "function") {
      elementos.modal.showModal();
    }
  }

  function cerrarModal() {
    if (elementos.modal) elementos.modal.close();
  }

  async function cargarSesion() {
    try {
      const respuesta = await fetch("/api/auth/yo");
      const datos = await respuesta.json();
      usuarioActual = datos.usuario || null;
    } catch (err) {
      console.error("Error consultando la sesión:", err);
      usuarioActual = null;
    }
    renderNavbar();
    return usuarioActual;
  }

  function mostrarError(elemento, mensaje) {
    elemento.textContent = mensaje;
    elemento.hidden = false;
  }

  async function enviarFormulario(endpoint, form, elementoError) {
    const datos = Object.fromEntries(new FormData(form).entries());

    try {
      const respuesta = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datos),
      });
      const cuerpo = await respuesta.json();

      if (!respuesta.ok) {
        mostrarError(elementoError, cuerpo.error || "Ocurrió un error.");
        return false;
      }

      usuarioActual = cuerpo.usuario;
      renderNavbar();
      cerrarModal();
      form.reset();
      listenersLogin.forEach((callback) => callback(usuarioActual));
      return true;
    } catch (err) {
      console.error(err);
      mostrarError(elementoError, "Ocurrió un error de conexión.");
      return false;
    }
  }

  async function cerrarSesion() {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } catch (err) {
      console.error("Error cerrando sesión:", err);
    }
    usuarioActual = null;
    renderNavbar();
    listenersLogout.forEach((callback) => callback());
  }

  function init() {
    cachearElementos();
    promesaListo = cargarSesion();

    if (elementos.abrirLoginBtn) {
      elementos.abrirLoginBtn.addEventListener("click", () => abrirModal("login"));
    }
    if (elementos.avatarMenu) {
      elementos.avatarMenu.addEventListener("click", () => RutaAvatar.pulsarMenu());
    }
    if (elementos.avatarBtn) {
      elementos.avatarBtn.addEventListener("click", () => {
        alternarMenu();
        RutaAvatar.pulsarBarra();
      });
      document.addEventListener("click", (evento) => {
        if (!elementos.usuarioInfo.contains(evento.target)) alternarMenu(false);
      });
      document.addEventListener("keydown", (evento) => {
        if (evento.key === "Escape" && !elementos.menuUsuario.hidden) {
          alternarMenu(false);
          elementos.avatarBtn.focus();
        }
      });
    }
    if (elementos.cerrarSesionBtn) {
      elementos.cerrarSesionBtn.addEventListener("click", cerrarSesion);
    }
    if (elementos.irARegistro) {
      elementos.irARegistro.addEventListener("click", (evento) => {
        evento.preventDefault();
        mostrarVista("registro");
      });
    }
    if (elementos.irALogin) {
      elementos.irALogin.addEventListener("click", (evento) => {
        evento.preventDefault();
        mostrarVista("login");
      });
    }
    if (elementos.formLogin) {
      elementos.formLogin.addEventListener("submit", (evento) => {
        evento.preventDefault();
        enviarFormulario("/api/auth/login", elementos.formLogin, elementos.errorLogin);
      });
    }
    if (elementos.formRegistro) {
      elementos.formRegistro.addEventListener("submit", (evento) => {
        evento.preventDefault();
        enviarFormulario("/api/auth/registro", elementos.formRegistro, elementos.errorRegistro);
      });
    }
  }

  return {
    init,
    cerrarMenu: () => alternarMenu(false),
    abrirModalLogin: () => abrirModal("login"),
    abrirModalRegistro: () => abrirModal("registro"),
    obtenerUsuarioActual: () => usuarioActual,
    listo: () => promesaListo,
    alIniciarSesion: (callback) => listenersLogin.push(callback),
    alCerrarSesion: (callback) => listenersLogout.push(callback),
  };
})();

document.addEventListener("DOMContentLoaded", () => RutaAuth.init());
