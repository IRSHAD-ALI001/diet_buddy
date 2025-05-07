import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import requests
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import json
import os
from datetime import datetime
import tempfile
from PIL import ImageTk, Image as PILImage
import io

# === Configuration ===
class Config:
    CACHE_DIR = "cache"
    CACHE_EXPIRY_DAYS = 7
    
    @classmethod
    def setup(cls):
        if not os.path.exists(cls.CACHE_DIR):
            os.makedirs(cls.CACHE_DIR)

# === AI Diet Generator ===
class DietGenerator:
    GEMINI_API_KEY = "AIzaSyAQ7Osd9Th7Yi9kvFkZ9SJGKilQXHmJm-M"  
    GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    
    @staticmethod
    def generate_diet(name, age, gender, weight, height, bmi_status, diet_intensity, diet_type, activity_level):
        prompt = (
            f"Create a detailed 7-day personalized Indian diet plan for {name}, a {age}-year-old {gender}.\n"
            f"Physical details: {weight}kg, {height}cm, BMI status: {bmi_status}.\n"
            f"Activity level: {activity_level}. Diet type: {diet_type}.\n"
            f"Diet intensity: {diet_intensity} approach.\n\n"
            "For each day, include:\n"
            "- Breakfast with detailed nutrition (calories, protein, carbs, fat, fiber)\n"
            "- Mid-morning snack with nutrition details\n"
            "- Lunch with detailed nutrition\n"
            "- Afternoon snack with nutrition details\n"
            "- Dinner with detailed nutrition\n"
            "- Optional evening snack with nutrition details\n\n"
            "For each meal, provide:\n"
            "- Exact quantities of each food item\n"
            "- Preparation method\n"
            "- Nutrition facts (calories, protein, carbs, fat, fiber)\n"
            "- Important micronutrients (vitamins, minerals)\n\n"
            "Provide a weekly summary with total calories and macros.\n"
            "Format the output with clear headings for each day and section."
        )
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        try:
            response = requests.post(DietGenerator.GEMINI_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            return f"Error generating diet: {str(e)}"

# === Visualization ===
class Charts:
    @staticmethod
    def create_bmi_figure(weight, height):
        bmi = weight / ((height / 100) ** 2)
        categories = ["Underweight (<18.5)", "Normal (18.5-24.9)", "Overweight (25-29.9)", "Obese (≥30)"]
        ranges = [18.5, 25, 30]
        colors = ["#3498db", "#2ecc71", "#f39c12", "#e74c3c"]
        
        # Determine BMI status and color
        if bmi < 18.5:
            status = categories[0]
            color = colors[0]
        elif 18.5 <= bmi < 25:
            status = categories[1]
            color = colors[1]
        elif 25 <= bmi < 30:
            status = categories[2]
            color = colors[2]
        else:
            status = categories[3]
            color = colors[3]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=["BMI"], y=[ranges[0]], name=categories[0], marker_color=colors[0]))
        fig.add_trace(go.Bar(x=["BMI"], y=[ranges[1]-ranges[0]], name=categories[1], marker_color=colors[1]))
        fig.add_trace(go.Bar(x=["BMI"], y=[ranges[2]-ranges[1]], name=categories[2], marker_color=colors[2]))
        fig.add_trace(go.Bar(x=["BMI"], y=[10], name=categories[3], marker_color=colors[3]))
        
        fig.add_trace(go.Scatter(
            x=["BMI"], y=[bmi], mode="markers+text",
            marker=dict(size=20, color=color),
            text=[f"Your BMI: {bmi:.1f} ({status})"], 
            textposition="top center",
            name="Your BMI",
            textfont=dict(size=14, color="black")
        ))
        
        fig.update_layout(
            title=f"BMI Classification - {status}",
            barmode="stack", 
            showlegend=False,
            yaxis_title="BMI Value", 
            yaxis_range=[10,40],
            plot_bgcolor='rgba(240,240,240,0.8)',
            paper_bgcolor='rgba(240,240,240,0.8)',
            margin=dict(l=20, r=20, t=60, b=20),
            height=350,
            title_font=dict(size=16, color='#2c3e50'),
            font=dict(family="Arial", size=12, color="#7f7f7f")
        )
        
        # Add range annotations
        fig.add_annotation(
            x=0.5, y=18.5/2,
            text="Underweight",
            showarrow=False,
            font=dict(color="white", size=10)
        )
        fig.add_annotation(
            x=0.5, y=18.5 + (25-18.5)/2,
            text="Normal",
            showarrow=False,
            font=dict(color="white", size=10)
        )
        fig.add_annotation(
            x=0.5, y=25 + (30-25)/2,
            text="Overweight",
            showarrow=False,
            font=dict(color="white", size=10)
        )
        fig.add_annotation(
            x=0.5, y=30 + (40-30)/2,
            text="Obese",
            showarrow=False,
            font=dict(color="white", size=10)
        )
        
        return fig
    
    @staticmethod
    def create_macro_figure(calories=2000, carbs=50, protein=30, fat=20):
        carbs_g = (carbs/100) * calories / 4
        protein_g = (protein/100) * calories / 4
        fat_g = (fat/100) * calories / 9
        
        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=["Carbs", "Protein", "Fat"], 
            values=[carbs, protein, fat],
            hole=0.4, 
            domain=dict(x=[0, 0.45]),
            marker_colors=["#636EFA", "#EF553B", "#00CC96"],
            textinfo='label+percent',
            textfont=dict(size=14, color='white'),
            hoverinfo='label+percent+value'
        ))
        fig.add_trace(go.Bar(
            x=["Carbs", "Protein", "Fat"], 
            y=[carbs_g, protein_g, fat_g],
            marker_color=["#636EFA", "#EF553B", "#00CC96"],
            xaxis="x2", 
            yaxis="y2",
            text=[f"{carbs_g:.1f}g", f"{protein_g:.1f}g", f"{fat_g:.1f}g"],
            textposition='auto',
            textfont=dict(size=12, color='black')
        ))
        
        fig.update_layout(
            title="Macronutrient Distribution",
            grid=dict(rows=1, columns=2, pattern="independent"),
            xaxis2=dict(domain=[0.55, 1.0]), 
            yaxis2=dict(domain=[0.1, 0.9]),
            showlegend=False,
            plot_bgcolor='rgba(240,240,240,0.8)',
            paper_bgcolor='rgba(240,240,240,0.8)',
            margin=dict(l=20, r=20, t=60, b=20),
            height=350,
            title_font=dict(size=16, color='#2c3e50'),
            font=dict(family="Arial", size=12, color="#7f7f7f")
        )
        
        return fig
    
    @staticmethod
    def save_figure(fig, filename):
        """Save figure to a temporary file and return path"""
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, filename)
        fig.write_image(filepath)
        return filepath

# === PDF Generator ===
class PDFGenerator:
    @staticmethod
    def generate_pdf(name, diet_text, weight, height):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Diet Plan"
        )
        
        if not file_path:
            return
        
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = Paragraph(f"<b>Personalized Diet Plan for {name}</b>", styles["Title"])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # User info
        bmi = weight / ((height / 100) ** 2)
        bmi_status = PDFGenerator.get_bmi_status(bmi)
        info_text = (
            f"<b>User Information:</b><br/>"
            f"Weight: {weight} kg<br/>Height: {height} cm<br/>BMI: {bmi:.1f} ({bmi_status})"
        )
        story.append(Paragraph(info_text, styles["Normal"]))
        story.append(Spacer(1, 24))
        
        # Diet plan
        story.append(Paragraph("<b>Diet Plan:</b>", styles["Heading2"]))
        for line in diet_text.split('\n'):
            if line.strip():
                story.append(Paragraph(line, styles["Normal"]))
                story.append(Spacer(1, 4))
        
        # Add charts
        try:
            fig = Charts.create_bmi_figure(weight, height)
            bmi_img_path = Charts.save_figure(fig, "bmi_chart.png")
            story.append(Spacer(1, 12))
            story.append(Paragraph("<b>BMI Analysis:</b>", styles["Heading2"]))
            story.append(Image(bmi_img_path, width=400, height=350))
            
            fig = Charts.create_macro_figure()
            macro_img_path = Charts.save_figure(fig, "macro_chart.png")
            story.append(Spacer(1, 12))
            story.append(Paragraph("<b>Recommended Macronutrients:</b>", styles["Heading2"]))
            story.append(Image(macro_img_path, width=400, height=350))
        except Exception as e:
            print(f"Error adding charts to PDF: {e}")
            story.append(Paragraph("<b>Charts could not be generated</b>", styles["Normal"]))
        
        doc.build(story)
        messagebox.showinfo("Success", f"PDF generated successfully at:\n{file_path}")
    
    @staticmethod
    def get_bmi_status(bmi):
        if bmi < 18.5:
            return "Underweight"
        elif 18.5 <= bmi < 25:
            return "Normal"
        elif 25 <= bmi < 30:
            return "Overweight"
        else:
            return "Obese"

# === Main Application ===
class DietBuddyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🍏 Diet Buddy - AI Nutrition Assistant")
        self.root.geometry("1000x800")
        self.root.configure(bg="#f5f9ff")
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        # Setup UI
        self.setup_ui()
        Config.setup()
        self.nutrition_data = {}  # To store nutrition details
    
    def configure_styles(self):
        """Configure custom styles for the application"""
        self.style.configure('.', background="#f5f9ff")
        self.style.configure('TFrame', background="#f5f9ff")
        self.style.configure('TLabel', background="#f5f9ff", foreground="#2c3e50", font=('Arial', 10))
        self.style.configure('Header.TLabel', font=('Arial', 16, 'bold'), foreground="#2980b9")
        self.style.configure('TButton', font=('Arial', 10), padding=5)
        self.style.map('TButton',
            foreground=[('active', '#ffffff'), ('!active', '#ffffff')],
            background=[('active', '#3498db'), ('!active', '#2980b9')],
            relief=[('pressed', 'sunken'), ('!pressed', 'raised')]
        )
        self.style.configure('TEntry', fieldbackground="#ffffff", width=20)
        self.style.configure('TCombobox', fieldbackground="#ffffff")
        self.style.configure('TText', background="#ffffff", foreground="#2c3e50")
    
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            header_frame, 
            text="🍏 Diet Buddy - AI Nutrition Assistant", 
            style="Header.TLabel"
        ).pack()
        
        # Button frame at the top
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("🍎 Generate Diet", self.generate_diet, "#27ae60"),
            ("📊 Show BMI Chart", self.show_bmi_chart, "#3498db"),
            ("📈 Show Macro Chart", self.show_macro_chart, "#9b59b6"),
            ("💾 Save PDF", self.save_pdf, "#e74c3c")
        ]
        
        for i, (text, command, color) in enumerate(buttons):
            btn = tk.Button(
                button_frame,
                text=text,
                command=command,
                bg=color,
                fg="white",
                activebackground=color,
                activeforeground="white",
                relief=tk.RAISED,
                bd=2,
                font=('Arial', 10, 'bold'),
                padx=5,
                pady=5
            )
            btn.grid(row=0, column=i, padx=2, sticky=tk.EW)
            button_frame.columnconfigure(i, weight=1)
        
        # Left panel (form) and right panel (output)
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Form
        left_panel = ttk.Frame(paned_window, width=300)
        paned_window.add(left_panel, weight=1)
        
        # Form frame
        form_frame = ttk.LabelFrame(left_panel, text="User Information", padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Form fields
        self.name_var = tk.StringVar()
        self.age_var = tk.StringVar()
        self.gender_var = tk.StringVar(value="male")
        self.weight_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self.diet_intensity_var = tk.StringVar(value="moderate")
        self.activity_var = tk.StringVar(value="moderate")
        self.diet_type_var = tk.StringVar(value="vegetarian")
        
        fields = [
            ("Name", self.name_var, None),
            ("Age", self.age_var, None),
            ("Gender", self.gender_var, ["male", "female", "other"]),
            ("Weight (kg)", self.weight_var, None),
            ("Height (cm)", self.height_var, None),
            ("Diet Intensity", self.diet_intensity_var, ["easy", "moderate", "hardcore"]),
            ("Activity Level", self.activity_var, ["sedentary", "light", "moderate", "active", "very active"]),
            ("Diet Type", self.diet_type_var, ["vegetarian", "non-vegetarian", "vegan"])
        ]
        
        for i, (label, var, options) in enumerate(fields):
            ttk.Label(form_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2, padx=5)
            if options:
                ttk.OptionMenu(form_frame, var, var.get(), *options).grid(row=i, column=1, sticky=tk.EW, pady=2, padx=5)
            else:
                ttk.Entry(form_frame, textvariable=var, width=20).grid(row=i, column=1, sticky=tk.EW, pady=2, padx=5)
            form_frame.columnconfigure(1, weight=1)
        
        # Right panel - Output
        right_panel = ttk.Frame(paned_window)
        paned_window.add(right_panel, weight=2)
        
        # Output notebook (tabs for diet and nutrition)
        self.output_notebook = ttk.Notebook(right_panel)
        self.output_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Diet plan tab
        diet_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(diet_frame, text="Diet Plan")
        
        self.diet_text = tk.Text(
            diet_frame,
            wrap=tk.WORD,
            font=("Arial", 10),
            padx=10,
            pady=10,
            bg="white",
            fg="black",
            relief=tk.SUNKEN,
            bd=2
        )
        diet_scrollbar = ttk.Scrollbar(diet_frame, command=self.diet_text.yview)
        self.diet_text.configure(yscrollcommand=diet_scrollbar.set)
        
        self.diet_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        diet_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Nutrition details tab
        nutrition_frame = ttk.Frame(self.output_notebook)
        self.output_notebook.add(nutrition_frame, text="Nutrition Details")
        
        self.nutrition_text = tk.Text(
            nutrition_frame,
            wrap=tk.WORD,
            font=("Arial", 10),
            padx=10,
            pady=10,
            bg="white",
            fg="black",
            relief=tk.SUNKEN,
            bd=2
        )
        nutrition_scrollbar = ttk.Scrollbar(nutrition_frame, command=self.nutrition_text.yview)
        self.nutrition_text.configure(yscrollcommand=nutrition_scrollbar.set)
        
        self.nutrition_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        nutrition_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def validate_inputs(self):
        try:
            if not self.name_var.get().strip():
                raise ValueError("Please enter your name")
            if not self.age_var.get().isdigit() or int(self.age_var.get()) < 10:
                raise ValueError("Please enter a valid age (10+)")
            if not self.weight_var.get().replace('.', '').isdigit() or float(self.weight_var.get()) <= 0:
                raise ValueError("Please enter a valid weight")
            if not self.height_var.get().replace('.', '').isdigit() or float(self.height_var.get()) <= 0:
                raise ValueError("Please enter a valid height")
            return True
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return False
    
    def get_bmi_status(self, bmi):
        if bmi < 18.5:
            return "Underweight (suggested goal: gain weight)"
        elif 18.5 <= bmi < 25:
            return "Normal (suggested goal: maintain weight)"
        elif 25 <= bmi < 30:
            return "Overweight (suggested goal: lose weight)"
        else:
            return "Obese (suggested goal: lose weight)"
    
    def extract_nutrition_data(self, diet_text):
        """Extract nutrition data from the diet plan text"""
        self.nutrition_data = {}
        
        # This is a simplified parser - in a real app you'd want more robust parsing
        days = diet_text.split("Day ")[1:]
        
        for day in days:
            day_num = day.split(":")[0].strip()
            self.nutrition_data[f"Day {day_num}"] = {}
            
            meals = day.split("\n\n")
            for meal in meals:
                if "Breakfast" in meal:
                    self.parse_meal_nutrition(meal, f"Day {day_num}", "Breakfast")
                elif "Lunch" in meal:
                    self.parse_meal_nutrition(meal, f"Day {day_num}", "Lunch")
                elif "Dinner" in meal:
                    self.parse_meal_nutrition(meal, f"Day {day_num}", "Dinner")
                elif "Snack" in meal:
                    self.parse_meal_nutrition(meal, f"Day {day_num}", "Snack")
    
    def parse_meal_nutrition(self, meal_text, day, meal_name):
        """Parse nutrition information from a meal text"""
        lines = meal_text.split("\n")
        nutrition = {
            "Calories": "N/A",
            "Protein": "N/A",
            "Carbs": "N/A",
            "Fat": "N/A",
            "Fiber": "N/A",
            "Micronutrients": []
        }
        
        for line in lines:
            line = line.strip()
            if "Calories:" in line:
                nutrition["Calories"] = line.split(":")[1].strip()
            elif "Protein:" in line:
                nutrition["Protein"] = line.split(":")[1].strip()
            elif "Carbs:" in line:
                nutrition["Carbs"] = line.split(":")[1].strip()
            elif "Fat:" in line:
                nutrition["Fat"] = line.split(":")[1].strip()
            elif "Fiber:" in line:
                nutrition["Fiber"] = line.split(":")[1].strip()
            elif "Vitamin" in line or "Mineral" in line:
                nutrition["Micronutrients"].append(line)
        
        self.nutrition_data[day][meal_name] = nutrition
    
    def display_nutrition_data(self):
        """Display the extracted nutrition data in the nutrition tab"""
        self.nutrition_text.delete(1.0, tk.END)
        
        if not self.nutrition_data:
            self.nutrition_text.insert(tk.END, "No nutrition data available. Please generate a diet plan first.")
            return
        
        for day, meals in self.nutrition_data.items():
            self.nutrition_text.insert(tk.END, f"\n{day}\n", "heading")
            self.nutrition_text.insert(tk.END, "="*50 + "\n")
            
            for meal_name, nutrition in meals.items():
                self.nutrition_text.insert(tk.END, f"\n{meal_name}\n", "subheading")
                self.nutrition_text.insert(tk.END, "-"*40 + "\n")
                
                self.nutrition_text.insert(tk.END, f"Calories: {nutrition['Calories']}\n")
                self.nutrition_text.insert(tk.END, f"Protein: {nutrition['Protein']}\n")
                self.nutrition_text.insert(tk.END, f"Carbs: {nutrition['Carbs']}\n")
                self.nutrition_text.insert(tk.END, f"Fat: {nutrition['Fat']}\n")
                self.nutrition_text.insert(tk.END, f"Fiber: {nutrition['Fiber']}\n")
                
                if nutrition["Micronutrients"]:
                    self.nutrition_text.insert(tk.END, "\nMicronutrients:\n")
                    for micro in nutrition["Micronutrients"]:
                        self.nutrition_text.insert(tk.END, f"- {micro}\n")
                
                self.nutrition_text.insert(tk.END, "\n")
        
        # Configure text tags for styling
        self.nutrition_text.tag_configure("heading", font=("Arial", 12, "bold"))
        self.nutrition_text.tag_configure("subheading", font=("Arial", 10, "bold"))
    
    def generate_diet(self):
        if not self.validate_inputs():
            return
        
        self.diet_text.delete(1.0, tk.END)
        self.diet_text.insert(tk.END, "Generating diet plan... Please wait...")
        self.root.update()
        
        try:
            weight = float(self.weight_var.get())
            height = float(self.height_var.get())
            bmi = weight / ((height / 100) ** 2)
            bmi_status = self.get_bmi_status(bmi)
            
            diet = DietGenerator.generate_diet(
                name=self.name_var.get(),
                age=int(self.age_var.get()),
                gender=self.gender_var.get(),
                weight=weight,
                height=height,
                bmi_status=bmi_status,
                diet_intensity=self.diet_intensity_var.get(),
                diet_type=self.diet_type_var.get(),
                activity_level=self.activity_var.get()
            )
            
            self.diet_text.delete(1.0, tk.END)
            self.diet_text.insert(tk.END, diet)
            
            # Extract and display nutrition data
            self.extract_nutrition_data(diet)
            self.display_nutrition_data()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate diet: {e}")
    
    def show_bmi_chart(self):
        if not self.validate_inputs():
            return
            
        try:
            weight = float(self.weight_var.get())
            height = float(self.height_var.get())
            fig = Charts.create_bmi_figure(weight, height)
            
            # Create a new window for the chart
            chart_window = tk.Toplevel(self.root)
            chart_window.title("BMI Analysis")
            chart_window.geometry("600x500")
            
            # Convert plotly figure to image
            img_bytes = fig.to_image(format="png")
            img = PILImage.open(io.BytesIO(img_bytes))
            img = ImageTk.PhotoImage(img)
            
            # Display the image
            label = ttk.Label(chart_window, image=img)
            label.image = img  # Keep a reference
            label.pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show BMI chart: {e}")
    
    def show_macro_chart(self):
        try:
            fig = Charts.create_macro_figure()
            
            # Create a new window for the chart
            chart_window = tk.Toplevel(self.root)
            chart_window.title("Macronutrient Distribution")
            chart_window.geometry("600x500")
            
            # Convert plotly figure to image
            img_bytes = fig.to_image(format="png")
            img = PILImage.open(io.BytesIO(img_bytes))
            img = ImageTk.PhotoImage(img)
            
            # Display the image
            label = ttk.Label(chart_window, image=img)
            label.image = img  # Keep a reference
            label.pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show macro chart: {e}")
    
    def save_pdf(self):
        if not self.validate_inputs():
            return
        
        try:
            weight = float(self.weight_var.get())
            height = float(self.height_var.get())
            diet_text = self.diet_text.get(1.0, tk.END)
            
            if not diet_text.strip() or "Generating diet plan" in diet_text:
                messagebox.showwarning("Warning", "Please generate a diet plan first")
                return
            
            PDFGenerator.generate_pdf(
                name=self.name_var.get(),
                diet_text=diet_text,
                weight=weight,
                height=height
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {e}")

# === Run Application ===
if __name__ == "__main__":
    try:
        import requests
        import plotly.graph_objects as go
        from PIL import ImageTk, Image as PILImage
    except ImportError:
        print("Please install required packages:")
        print("pip install requests plotly pillow reportlab")
        exit(1)
    
    root = tk.Tk()
    app = DietBuddyApp(root)
    root.mainloop()