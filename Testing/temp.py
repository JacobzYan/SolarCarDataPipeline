import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# Function to generate the first plot
def plot_sine_wave():
    x = np.linspace(0, 2 * np.pi, 100)
    y = np.sin(x)
    
    fig, ax = plt.subplots()
    ax.plot(x, y, label='sin(x)')
    ax.set_title('Sine Wave')
    ax.set_xlabel('x')
    ax.set_ylabel('sin(x)')
    ax.legend()
    
    return fig

# Function to generate the second plot
def plot_cosine_wave():
    x = np.linspace(0, 2 * np.pi, 100)
    y = np.cos(x)
    
    fig, ax = plt.subplots()
    ax.plot(x, y, label='cos(x)', color='orange')
    ax.set_title('Cosine Wave')
    ax.set_xlabel('x')
    ax.set_ylabel('cos(x)')
    ax.legend()
    
    return fig

# Function to generate the third plot
def plot_random_walk():
    np.random.seed(0)
    y = np.cumsum(np.random.randn(100))
    
    fig, ax = plt.subplots()
    ax.plot(y, label='Random Walk', color='green')
    ax.set_title('Random Walk')
    ax.set_xlabel('Step')
    ax.set_ylabel('Value')
    ax.legend()
    
    return fig

# Function to generate the fourth plot
def plot_exponential_decay():
    x = np.linspace(0, 5, 100)
    y = np.exp(-x)
    
    fig, ax = plt.subplots()
    ax.plot(x, y, label='exp(-x)', color='red')
    ax.set_title('Exponential Decay')
    ax.set_xlabel('x')
    ax.set_ylabel('exp(-x)')
    ax.legend()
    
    return fig

# Streamlit App layout
def main():
    st.title("Multiple Separate Matplotlib Plots in Streamlit")
    
    st.subheader("Sine Wave Plot")
    fig_sine = plot_sine_wave()
    st.pyplot(fig_sine)
    
    st.subheader("Cosine Wave Plot")
    fig_cosine = plot_cosine_wave()
    st.pyplot(fig_cosine)
    
    st.subheader("Random Walk Plot")
    fig_walk = plot_random_walk()
    st.pyplot(fig_walk)
    
    st.subheader("Exponential Decay Plot")
    fig_exp = plot_exponential_decay()
    st.pyplot(fig_exp)

# Run the app
if __name__ == "__main__":
    main()
