package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"

	"github.com/fatih/color"
	"github.com/spf13/cobra"
)

var (
	apiURL  string
	token   string
	verbose bool
)

func main() {
	rootCmd := &cobra.Command{
		Use:   "iot-cli",
		Short: "IoT Platform CLI - API testing and management tool",
		Long:  `A Go-based CLI tool for testing and managing the IoT Platform API.`,
	}

	// Global flags
	rootCmd.PersistentFlags().StringVarP(&apiURL, "api", "a", "", "API Gateway URL (or IOT_API_URL env)")
	rootCmd.PersistentFlags().StringVarP(&token, "token", "t", "", "JWT token (or IOT_TOKEN env)")
	rootCmd.PersistentFlags().BoolVarP(&verbose, "verbose", "v", false, "Verbose output")

	// Commands
	rootCmd.AddCommand(healthCmd())
	rootCmd.AddCommand(loginCmd())
	rootCmd.AddCommand(devicesCmd())
	rootCmd.AddCommand(telemetryCmd())
	rootCmd.AddCommand(loadTestCmd())

	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

func getAPIURL() string {
	if apiURL != "" {
		return apiURL
	}
	return os.Getenv("IOT_API_URL")
}

func getToken() string {
	if token != "" {
		return token
	}
	return os.Getenv("IOT_TOKEN")
}

// ============================================
// HEALTH CHECK
// ============================================
func healthCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "health",
		Short: "Check API health status",
		Run: func(cmd *cobra.Command, args []string) {
			url := getAPIURL()
			if url == "" {
				color.Red("API URL not set. Use --api flag or IOT_API_URL env")
				os.Exit(1)
			}

			start := time.Now()
			resp, err := http.Get(url + "/api/user")
			elapsed := time.Since(start)

			if err != nil {
				color.Red("✗ API unreachable: %v", err)
				os.Exit(1)
			}
			defer resp.Body.Close()

			if resp.StatusCode < 500 {
				color.Green("✓ API is healthy")
				fmt.Printf("  Status: %d\n", resp.StatusCode)
				fmt.Printf("  Latency: %v\n", elapsed)
			} else {
				color.Red("✗ API error: %d", resp.StatusCode)
			}
		},
	}
}

// ============================================
// LOGIN
// ============================================
func loginCmd() *cobra.Command {
	var email, password string

	cmd := &cobra.Command{
		Use:   "login",
		Short: "Authenticate and get JWT token",
		Run: func(cmd *cobra.Command, args []string) {
			url := getAPIURL()
			if url == "" {
				color.Red("API URL not set")
				os.Exit(1)
			}

			payload := map[string]string{
				"email":    email,
				"password": password,
			}
			body, _ := json.Marshal(payload)

			resp, err := http.Post(url+"/api/user/login", "application/json", bytes.NewBuffer(body))
			if err != nil {
				color.Red("Login failed: %v", err)
				os.Exit(1)
			}
			defer resp.Body.Close()

			respBody, _ := io.ReadAll(resp.Body)
			var result map[string]interface{}
			json.Unmarshal(respBody, &result)

			if resp.StatusCode == 200 {
				color.Green("✓ Login successful")
				if token, ok := result["token"].(string); ok {
					fmt.Printf("\nExport token:\nexport IOT_TOKEN=\"%s\"\n", token)
				}
			} else {
				color.Red("✗ Login failed: %v", result["message"])
			}
		},
	}

	cmd.Flags().StringVarP(&email, "email", "e", "", "Email address")
	cmd.Flags().StringVarP(&password, "password", "p", "", "Password")
	cmd.MarkFlagRequired("email")
	cmd.MarkFlagRequired("password")

	return cmd
}

// ============================================
// DEVICES
// ============================================
func devicesCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "devices",
		Short: "Manage devices",
	}

	listCmd := &cobra.Command{
		Use:   "list",
		Short: "List all devices",
		Run: func(cmd *cobra.Command, args []string) {
			makeAuthenticatedRequest("GET", "/api/devices", nil)
		},
	}

	cmd.AddCommand(listCmd)
	return cmd
}

// ============================================
// TELEMETRY
// ============================================
func telemetryCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "telemetry",
		Short: "Manage telemetry data",
	}

	var deviceID string
	var temperature, humidity float64

	sendCmd := &cobra.Command{
		Use:   "send",
		Short: "Send telemetry data",
		Run: func(cmd *cobra.Command, args []string) {
			payload := map[string]interface{}{
				"deviceId":    deviceID,
				"temperature": temperature,
				"humidity":    humidity,
			}
			body, _ := json.Marshal(payload)
			makeAuthenticatedRequest("POST", "/api/telemetry?deviceId="+deviceID, body)
		},
	}
	sendCmd.Flags().StringVarP(&deviceID, "device", "d", "", "Device ID")
	sendCmd.Flags().Float64VarP(&temperature, "temp", "T", 25.0, "Temperature value")
	sendCmd.Flags().Float64VarP(&humidity, "humidity", "H", 50.0, "Humidity value")
	sendCmd.MarkFlagRequired("device")

	cmd.AddCommand(sendCmd)
	return cmd
}

// ============================================
// LOAD TEST
// ============================================
func loadTestCmd() *cobra.Command {
	var requests, concurrency int
	var deviceID string

	cmd := &cobra.Command{
		Use:   "loadtest",
		Short: "Run load test against telemetry endpoint",
		Run: func(cmd *cobra.Command, args []string) {
			url := getAPIURL()
			if url == "" {
				color.Red("API URL not set")
				os.Exit(1)
			}

			color.Cyan("Starting load test: %d requests, %d concurrent", requests, concurrency)

			results := make(chan time.Duration, requests)
			errors := make(chan error, requests)

			start := time.Now()

			// Worker pool
			sem := make(chan struct{}, concurrency)
			for i := 0; i < requests; i++ {
				sem <- struct{}{}
				go func(n int) {
					defer func() { <-sem }()

					payload := map[string]interface{}{
						"deviceId":    deviceID,
						"temperature": 20.0 + float64(n%10),
						"humidity":    50.0 + float64(n%20),
					}
					body, _ := json.Marshal(payload)

					reqStart := time.Now()
					resp, err := http.Post(url+"/api/telemetry?deviceId="+deviceID, "application/json", bytes.NewBuffer(body))
					elapsed := time.Since(reqStart)

					if err != nil {
						errors <- err
						return
					}
					resp.Body.Close()

					if resp.StatusCode >= 400 {
						errors <- fmt.Errorf("status %d", resp.StatusCode)
						return
					}

					results <- elapsed
				}(i)
			}

			// Wait for completion
			for i := 0; i < concurrency; i++ {
				sem <- struct{}{}
			}

			close(results)
			close(errors)

			// Calculate stats
			var total time.Duration
			var count int
			var min, max time.Duration = time.Hour, 0

			for d := range results {
				total += d
				count++
				if d < min {
					min = d
				}
				if d > max {
					max = d
				}
			}

			errorCount := len(errors)
			totalTime := time.Since(start)

			color.Green("\n=== Load Test Results ===")
			fmt.Printf("Total requests: %d\n", requests)
			fmt.Printf("Successful: %d\n", count)
			fmt.Printf("Failed: %d\n", errorCount)
			fmt.Printf("Total time: %v\n", totalTime)
			if count > 0 {
				fmt.Printf("Avg latency: %v\n", total/time.Duration(count))
				fmt.Printf("Min latency: %v\n", min)
				fmt.Printf("Max latency: %v\n", max)
				fmt.Printf("Requests/sec: %.2f\n", float64(count)/totalTime.Seconds())
			}
		},
	}

	cmd.Flags().IntVarP(&requests, "requests", "n", 100, "Number of requests")
	cmd.Flags().IntVarP(&concurrency, "concurrency", "c", 10, "Concurrent requests")
	cmd.Flags().StringVarP(&deviceID, "device", "d", "", "Device ID for testing")
	cmd.MarkFlagRequired("device")

	return cmd
}

// ============================================
// HELPERS
// ============================================
func makeAuthenticatedRequest(method, path string, body []byte) {
	url := getAPIURL()
	tkn := getToken()

	if url == "" {
		color.Red("API URL not set")
		os.Exit(1)
	}

	var req *http.Request
	var err error

	if body != nil {
		req, err = http.NewRequest(method, url+path, bytes.NewBuffer(body))
	} else {
		req, err = http.NewRequest(method, url+path, nil)
	}

	if err != nil {
		color.Red("Request error: %v", err)
		os.Exit(1)
	}

	req.Header.Set("Content-Type", "application/json")
	if tkn != "" {
		req.Header.Set("Authorization", "Bearer "+tkn)
	}

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		color.Red("Request failed: %v", err)
		os.Exit(1)
	}
	defer resp.Body.Close()

	respBody, _ := io.ReadAll(resp.Body)

	if verbose {
		fmt.Printf("Status: %d\n", resp.StatusCode)
	}

	var prettyJSON bytes.Buffer
	if json.Indent(&prettyJSON, respBody, "", "  ") == nil {
		fmt.Println(prettyJSON.String())
	} else {
		fmt.Println(string(respBody))
	}
}
