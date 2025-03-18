import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np

# Fonction pour initialiser GLFW et créer une fenêtre
def create_window():
    if not glfw.init():
        raise Exception("GLFW ne peut pas être initialisé")

    window = glfw.create_window(1280, 1280, "Fractale", None, None)
    if not window:
        glfw.terminate()
        raise Exception("La fenêtre GLFW n'a pas pu être créée")

    glfw.make_context_current(window)
    return window


# Code du vertex shader
vertex_shader_code = """
#version 330
in vec2 position;
out vec2 fragCoord;
void main() {
    gl_Position = vec4(position, 0.0, 1.0);
    fragCoord = position * 0.5 + 0.5;
}
"""

# Code du fragment shader modifié pour inclure différentes fractales
fragment_shader_code = """
#version 330
out vec4 color;
in vec2 fragCoord;

uniform float zoom;
uniform vec2 offset;
uniform float maxIterations;
uniform int fractale_type;  // Type de fractale

// Fonction de calcul de la fractale de Mandelbrot
vec2 mandelbrot(vec2 c) {
    vec2 z = vec2(0.0, 0.0);
    int i;
    for (i = 0; i < maxIterations; ++i) {
        if (dot(z, z) > 16.0) break;
        z = vec2(z.x * z.x - z.y * z.y, 2.0 * z.x * z.y) + c;
    }
    return vec2(float(i) / float(maxIterations), 0.0);
}

// Fonction de calcul de la fractale de Julia
vec2 julia(vec2 c, vec2 constant) {
    vec2 z = c;
    int i;
    for (i = 0; i < maxIterations; ++i) {
        if (dot(z, z) > 16.0) break;
        z = vec2(z.x * z.x - z.y * z.y, 2.0 * z.x * z.y) + constant;
    }
    return vec2(float(i) / float(maxIterations), 0.0);
}

// Fonction principale
void main() {
    vec2 c = (fragCoord - 0.5) * zoom + offset;

    vec2 result = vec2(0.0);

    // Sélectionner la fractale selon le type
    if (fractale_type == 0) {
        result = mandelbrot(c);
    } else if (fractale_type == 1) {
        result = julia(c, vec2(0.355, 0.355));  // Exemple pour Julia
    }

    // Calcul de la couleur
    color = vec4(result.x, result.x * 0.5, result.x * 0.25, 1.0);
}
"""


# Fonction pour créer et compiler les shaders
def create_shader_program():
    vertex_shader = compileShader(vertex_shader_code, GL_VERTEX_SHADER)
    fragment_shader = compileShader(fragment_shader_code, GL_FRAGMENT_SHADER)
    shader_program = compileProgram(vertex_shader, fragment_shader)
    return shader_program


# Fonction principale pour afficher la fractale
def main():
    window = create_window()
    shader_program = create_shader_program()

    # Coordonnées des sommets pour couvrir l'écran entier
    vertices = np.array([
        -1.0, -1.0,
        1.0, -1.0,
        1.0, 1.0,
        -1.0, 1.0
    ], dtype=np.float32)

    # Création du VBO et du VAO
    VAO = glGenVertexArrays(1)
    VBO = glGenBuffers(1)

    glBindVertexArray(VAO)
    glBindBuffer(GL_ARRAY_BUFFER, VBO)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    # Position des sommets
    position = glGetAttribLocation(shader_program, "position")
    glVertexAttribPointer(position, 2, GL_FLOAT, GL_FALSE, 2 * 4, ctypes.c_void_p(0))
    glEnableVertexAttribArray(position)

    # Paramètres du zoom et du décalage (offset) pour la fractale
    zoom = 1.0
    offset = np.array([0.0, 0.0], dtype=np.float32)
    maxIterations = 128  # Un nombre d'itérations raisonnable pour la qualité

    # Variables pour le drag and drop
    is_dragging = False
    last_mouse_pos = np.array([0.0, 0.0], dtype=np.float32)

    # Fonction de gestion de la molette de la souris pour zoomer
    def mouse_scroll_callback(window, xoffset, yoffset):
        nonlocal zoom
        zoom *= 1.1 ** yoffset  # Zoom avant ou arrière avec la molette

    # Fonction pour gérer le début du drag
    def mouse_button_callback(window, button, action, mods):
        nonlocal is_dragging, last_mouse_pos
        if button == glfw.MOUSE_BUTTON_LEFT:
            if action == glfw.PRESS:
                is_dragging = True
                # Obtenir la position de la souris
                last_mouse_pos = np.array(glfw.get_cursor_pos(window), dtype=np.float32)
            elif action == glfw.RELEASE:
                is_dragging = False

    # Fonction pour gérer le mouvement de la souris pendant le drag
    def mouse_move_callback(window, xpos, ypos):
        nonlocal is_dragging, offset, last_mouse_pos
        if is_dragging:
            # Calcul du déplacement de la souris
            delta = np.array([xpos, ypos], dtype=np.float32) - last_mouse_pos
            offset += delta * zoom * 0.005  # Ajuster la vitesse de déplacement
            last_mouse_pos = np.array([xpos, ypos], dtype=np.float32)

    glfw.set_scroll_callback(window, mouse_scroll_callback)
    glfw.set_mouse_button_callback(window, mouse_button_callback)
    glfw.set_cursor_pos_callback(window, mouse_move_callback)

    # Choisir le type de fractale (0 pour Mandelbrot, 1 pour Julia, etc.)
    fractale_type = 0  # Changez cette valeur pour tester différentes fractales

    # Boucle de rendu
    while not glfw.window_should_close(window):
        glClear(GL_COLOR_BUFFER_BIT)

        # Utiliser le programme de shaders
        glUseProgram(shader_program)

        # Passer les paramètres du zoom, de l'offset, du nombre d'itérations et du type de fractale au shader
        glUniform1f(glGetUniformLocation(shader_program, "zoom"), zoom)
        glUniform2fv(glGetUniformLocation(shader_program, "offset"), 1, offset)
        glUniform1f(glGetUniformLocation(shader_program, "maxIterations"), maxIterations)
        glUniform1i(glGetUniformLocation(shader_program, "fractale_type"), fractale_type)

        # Dessiner la fractale
        glBindVertexArray(VAO)
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

        # Échanger les buffers
        glfw.swap_buffers(window)

        # Vérifier les événements
        glfw.poll_events()

    # Nettoyer et fermer la fenêtre
    glfw.terminate()


if __name__ == "__main__":
    main()
