// Registro/login (nombre + apellido + PIN de 4 dígitos, sin correo) y
// estado de sesión, compartido con main.js a través de window.RutaAuth.

const RutaAuth = (() => {
  let usuarioActual = null;
  let promesaListo = null;
  const listenersLogin = [];

  const elementos = {};

  function cachearElementos() {
    elementos.modal = document.querySelector("[data-modal-auth]");
    elementos.widget = document.querySelector("[data-auth-widget]");
    elementos.abrirLoginBtn = document.querySelector("[data-abrir-login]");
    elementos.cerrarSesionBtn = document.querySelector("[data-cerrar-sesion]");
    elementos.usuarioInfo = document.querySelector("[data-usuario-info]");
    elementos.usuarioNombre = document.querySelector("[data-usuario-nombre]");
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
      elementos.usuarioNombre.textContent = `Hola, ${usuarioActual.nombre}`;
    }
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
  }

  function init() {
    cachearElementos();
    promesaListo = cargarSesion();

    if (elementos.abrirLoginBtn) {
      elementos.abrirLoginBtn.addEventListener("click", () => abrirModal("login"));
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
    abrirModalLogin: () => abrirModal("login"),
    obtenerUsuarioActual: () => usuarioActual,
    listo: () => promesaListo,
    alIniciarSesion: (callback) => listenersLogin.push(callback),
  };
})();

document.addEventListener("DOMContentLoaded", () => RutaAuth.init());
