import pygame

class GUI:
    def __init__(self):
        pygame.init()
        
        # Create the window
        self.width, self.height = 400, 300
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Python GUI Example")

        # Font for displaying text
        self.font = pygame.font.Font(None, 36)
        self.text = "Waiting for data..."

        self.running = True

    def set_received_text(self, text):
        """Update the displayed text."""
        self.text = text

    def run(self):
        """Main loop to display the GUI."""
        while self.running:
            self.screen.fill((255, 255, 255))  # White background

            # Render the text
            rendered_text = self.font.render(self.text, True, (0, 0, 0))
            self.screen.blit(rendered_text, (50, 50))

            # Event handling
