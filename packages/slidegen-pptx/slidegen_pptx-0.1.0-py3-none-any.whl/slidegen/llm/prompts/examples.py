"""Few-shot examples for LLM schema generation."""

FEW_SHOT_EXAMPLES = [
    {
        "user": "Create a presentation about Q4 financial results with a title slide, key metrics, and a revenue chart",
        "assistant": """presentation:
  title: "Q4 Financial Results"
  slides:
    - layout: title
      title: "Q4 Financial Results"
      subtitle: "Year-End Review"
    
    - layout: bullet_list
      title: "Key Metrics"
      bullets:
        - "Revenue: $125M (+15% YoY)"
        - "Profit margin: 22%"
        - "Customer growth: +1.2M users"
    
    - layout: chart
      title: "Revenue Trend"
      chart:
        type: line
        data:
          labels: ["Q1", "Q2", "Q3", "Q4"]
          values: [100, 120, 140, 160]
        x_axis_label: "Quarter"
        y_axis_label: "Revenue ($M)"
"""
    },
    {
        "user": "Make a product roadmap presentation with sections for Q1, Q2, Q3, and Q4 priorities",
        "assistant": """presentation:
  title: "Product Roadmap 2026"
  slides:
    - layout: title
      title: "Product Roadmap 2026"
      subtitle: "Building the Future"
    
    - layout: section_header
      text: "Q1 2026: Foundation"
    
    - layout: bullet_list
      title: "Q1 Priorities"
      bullets:
        - "Performance optimization"
        - "Security audit"
        - "Developer experience improvements"
    
    - layout: section_header
      text: "Q2 2026: Intelligence"
    
    - layout: bullet_list
      title: "Q2 Priorities"
      bullets:
        - "AI-powered features"
        - "Predictive analytics"
        - "Smart recommendations"
    
    - layout: section_header
      text: "Q3 2026: Collaboration"
    
    - layout: bullet_list
      title: "Q3 Priorities"
      bullets:
        - "Real-time collaboration"
        - "Team workspaces"
        - "Activity feed"
    
    - layout: section_header
      text: "Q4 2026: Scale"
    
    - layout: bullet_list
      title: "Q4 Priorities"
      bullets:
        - "Enterprise features"
        - "API marketplace"
        - "Advanced reporting"
"""
    },
    {
        "user": "Create a before and after comparison slide showing manual vs automated process",
        "assistant": """presentation:
  title: "Process Comparison"
  slides:
    - layout: title
      title: "Process Improvement"
      subtitle: "Before vs After"
    
    - layout: comparison
      title: "Manual vs Automated Process"
      before:
        type: bullet_list
        bullets:
          - "Manual reporting: 8 hours/week"
          - "Data in 5 separate systems"
          - "Reactive decision-making"
      after:
        type: bullet_list
        bullets:
          - "Automated reporting: 30 minutes/week"
          - "Unified data platform"
          - "Data-driven insights"
"""
    },
    {
        "user": "Make a slide with two columns showing benefits on the left and features on the right",
        "assistant": """presentation:
  title: "Product Overview"
  slides:
    - layout: title
      title: "Product Overview"
    
    - layout: two_column
      title: "Benefits & Features"
      left:
        type: bullet_list
        bullets:
          - "Saves time"
          - "Increases productivity"
          - "Reduces errors"
      right:
        type: bullet_list
        bullets:
          - "Feature 1"
          - "Feature 2"
          - "Feature 3"
"""
    },
    {
        "user": "Create a presentation with a quote slide featuring a customer testimonial",
        "assistant": """presentation:
  title: "Customer Testimonials"
  slides:
    - layout: title
      title: "What Our Customers Say"
    
    - layout: quote
      quote:
        text: "This product has transformed how we work. It's a game-changer."
        attribution: "Sarah Johnson, CEO at Acme Corp"
"""
    },
    {
        "user": "Make a data analysis slide with a table showing sales by region",
        "assistant": """presentation:
  title: "Sales Analysis"
  slides:
    - layout: title
      title: "Sales Analysis"
    
    - layout: table
      title: "Sales by Region"
      table:
        data:
          - ["Region", "Q1", "Q2", "Q3", "Q4"]
          - ["North", "100", "120", "140", "160"]
          - ["South", "80", "90", "110", "130"]
          - ["East", "90", "100", "120", "140"]
          - ["West", "110", "130", "150", "170"]
        header_row: true
"""
    },
    {
        "user": "Create a presentation about our team with an image slide showing the team photo",
        "assistant": """presentation:
  title: "Our Team"
  slides:
    - layout: title
      title: "Meet Our Team"
      subtitle: "The People Behind the Product"
    
    - layout: image
      title: "Team Photo"
      image:
        src: "team-photo.jpg"
        alt: "Our team members"
        caption: "The SlideGen team at our annual retreat"
"""
    },
    {
        "user": "Make a training presentation with section headers for each module",
        "assistant": """presentation:
  title: "Training Program"
  slides:
    - layout: title
      title: "Effective Communication Training"
      subtitle: "Building Stronger Teams"
    
    - layout: section_header
      text: "Module 1: Introduction"
    
    - layout: bullet_list
      title: "Learning Objectives"
      bullets:
        - "Understand communication styles"
        - "Learn active listening techniques"
        - "Practice giving feedback"
    
    - layout: section_header
      text: "Module 2: Best Practices"
    
    - layout: bullet_list
      title: "Key Principles"
      bullets:
        - "Be clear and concise"
        - "Listen actively"
        - "Ask clarifying questions"
"""
    },
    {
        "user": "Create a presentation with multiple chart types: bar chart for revenue, pie chart for market share",
        "assistant": """presentation:
  title: "Business Analysis"
  slides:
    - layout: title
      title: "Business Analysis"
    
    - layout: chart
      title: "Revenue by Product"
      chart:
        type: bar
        data:
          labels: ["Product A", "Product B", "Product C"]
          values: [100, 150, 120]
        x_axis_label: "Product"
        y_axis_label: "Revenue ($M)"
    
    - layout: chart
      title: "Market Share"
      chart:
        type: pie
        data:
          labels: ["Us", "Competitor 1", "Competitor 2", "Others"]
          values: [35, 25, 20, 20]
"""
    },
    {
        "user": "Make a simple title slide for a company meeting",
        "assistant": """presentation:
  title: "Company Meeting"
  slides:
    - layout: title
      title: "Company Meeting"
      subtitle: "January 2026"
"""
    }
]


def get_few_shot_examples() -> list:
    """
    Get few-shot examples for LLM schema generation.
    
    Returns:
        List of example conversations (user request, assistant schema)
    """
    return FEW_SHOT_EXAMPLES


def get_examples_by_layout(layout_type: str) -> list:
    """
    Get examples that demonstrate a specific layout type.
    
    Args:
        layout_type: The layout type to filter by
        
    Returns:
        List of examples using the specified layout
    """
    layout_keywords = {
        "title": ["title", "title slide"],
        "section_header": ["section", "header", "divider"],
        "bullet_list": ["bullet", "list", "points", "items"],
        "two_column": ["two column", "side by side", "columns"],
        "comparison": ["before", "after", "compare", "comparison"],
        "image": ["image", "photo", "picture"],
        "chart": ["chart", "graph", "visualization", "data"],
        "table": ["table", "data table", "tabular"],
        "quote": ["quote", "testimonial", "attribution"],
        "blank": ["blank", "empty"],
    }
    
    keywords = layout_keywords.get(layout_type, [])
    return [
        ex for ex in FEW_SHOT_EXAMPLES
        if any(keyword in ex["user"].lower() or keyword in ex["assistant"].lower() 
               for keyword in keywords)
    ]

