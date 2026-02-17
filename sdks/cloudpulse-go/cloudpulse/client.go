// Package cloudpulse provides a Go client for the CloudPulse v2 API.
//
// Usage:
//
//	client := cloudpulse.NewClient("cpls_...")
//	workspaces, err := client.Workspaces.List(nil)
package cloudpulse

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"
)

const (
	DefaultBaseURL = "https://api.cloudpulse.dev"
	APIVersion     = "v2"
	UserAgent      = "cloudpulse-go/0.1.0"
)

// Client is the CloudPulse API client.
type Client struct {
	BaseURL    string
	APIToken   string
	HTTPClient *http.Client

	Workspaces    *WorkspacesService
	CostReports   *CostReportsService
	Folders       *FoldersService
	Segments      *SegmentsService
	Teams         *TeamsService
	VirtualTags   *VirtualTagsService
	APITokens     *APITokensService
}

// NewClient creates a new CloudPulse API client.
func NewClient(apiToken string) *Client {
	c := &Client{
		BaseURL:    fmt.Sprintf("%s/api/%s", DefaultBaseURL, APIVersion),
		APIToken:   apiToken,
		HTTPClient: &http.Client{Timeout: 30 * time.Second},
	}
	c.Workspaces = &WorkspacesService{client: c}
	c.CostReports = &CostReportsService{client: c}
	c.Folders = &FoldersService{client: c}
	c.Segments = &SegmentsService{client: c}
	c.Teams = &TeamsService{client: c}
	c.VirtualTags = &VirtualTagsService{client: c}
	c.APITokens = &APITokensService{client: c}
	return c
}

func (c *Client) doRequest(method, path string, body interface{}) ([]byte, error) {
	var buf io.Reader
	if body != nil {
		b, err := json.Marshal(body)
		if err != nil {
			return nil, err
		}
		buf = bytes.NewBuffer(b)
	}

	req, err := http.NewRequest(method, c.BaseURL+path, buf)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+c.APIToken)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("User-Agent", UserAgent)

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("API error %d: %s", resp.StatusCode, string(data))
	}

	return data, nil
}

// --- Models ---

type Workspace struct {
	Token     string `json:"token"`
	Name      string `json:"name"`
	IsDefault bool   `json:"is_default"`
	CreatedAt string `json:"created_at"`
}

type WorkspaceList struct {
	Workspaces []Workspace       `json:"workspaces"`
	Links      map[string]string `json:"links"`
}

type CostReport struct {
	Token        string                 `json:"token"`
	Title        string                 `json:"title"`
	Filter       string                 `json:"filter,omitempty"`
	Groupings    string                 `json:"groupings"`
	DateInterval string                 `json:"date_interval"`
	DateBucket   string                 `json:"date_bucket"`
	Settings     map[string]interface{} `json:"settings"`
	CreatedAt    string                 `json:"created_at"`
}

type CostReportList struct {
	CostReports []CostReport      `json:"cost_reports"`
	Links       map[string]string `json:"links"`
}

type Folder struct {
	Token     string `json:"token"`
	Title     string `json:"title"`
	CreatedAt string `json:"created_at"`
}

type FolderList struct {
	Folders []Folder          `json:"folders"`
	Links   map[string]string `json:"links"`
}

type Segment struct {
	Token            string `json:"token"`
	Title            string `json:"title"`
	Description      string `json:"description,omitempty"`
	Filter           string `json:"filter,omitempty"`
	Priority         int    `json:"priority"`
	TrackUnallocated bool   `json:"track_unallocated"`
	CreatedAt        string `json:"created_at"`
}

type SegmentList struct {
	Segments []Segment         `json:"segments"`
	Links    map[string]string `json:"links"`
}

type Team struct {
	Token       string `json:"token"`
	Name        string `json:"name"`
	Description string `json:"description,omitempty"`
	CreatedAt   string `json:"created_at"`
}

type TeamList struct {
	Teams []Team            `json:"teams"`
	Links map[string]string `json:"links"`
}

type VirtualTag struct {
	Token       string                   `json:"token"`
	Key         string                   `json:"key"`
	Description string                   `json:"description,omitempty"`
	Overridable bool                     `json:"overridable"`
	Values      []map[string]interface{} `json:"values"`
	CreatedAt   string                   `json:"created_at"`
}

type VirtualTagList struct {
	VirtualTags []VirtualTag      `json:"virtual_tags"`
	Links       map[string]string `json:"links"`
}

type APITokenResponse struct {
	TokenPrefix string `json:"token_prefix"`
	Name        string `json:"name"`
	Scopes      string `json:"scopes"`
	IsActive    bool   `json:"is_active"`
	CreatedAt   string `json:"created_at"`
}

type APITokenCreated struct {
	APITokenResponse
	Token string `json:"token"`
}

type Message struct {
	Message string `json:"message"`
}

type ListParams struct {
	Page           int
	Limit          int
	WorkspaceToken string
}

func (p *ListParams) toQuery() string {
	v := url.Values{}
	if p != nil {
		if p.Page > 0 {
			v.Set("page", fmt.Sprintf("%d", p.Page))
		}
		if p.Limit > 0 {
			v.Set("limit", fmt.Sprintf("%d", p.Limit))
		}
		if p.WorkspaceToken != "" {
			v.Set("workspace_token", p.WorkspaceToken)
		}
	}
	if len(v) > 0 {
		return "?" + v.Encode()
	}
	return ""
}

// --- Services ---

type WorkspacesService struct{ client *Client }

func (s *WorkspacesService) List(params *ListParams) (*WorkspaceList, error) {
	data, err := s.client.doRequest("GET", "/workspaces"+params.toQuery(), nil)
	if err != nil { return nil, err }
	var result WorkspaceList
	return &result, json.Unmarshal(data, &result)
}

func (s *WorkspacesService) Get(token string) (*Workspace, error) {
	data, err := s.client.doRequest("GET", "/workspaces/"+token, nil)
	if err != nil { return nil, err }
	var result Workspace
	return &result, json.Unmarshal(data, &result)
}

func (s *WorkspacesService) Create(body map[string]interface{}) (*Workspace, error) {
	data, err := s.client.doRequest("POST", "/workspaces", body)
	if err != nil { return nil, err }
	var result Workspace
	return &result, json.Unmarshal(data, &result)
}

func (s *WorkspacesService) Delete(token string) (*Message, error) {
	data, err := s.client.doRequest("DELETE", "/workspaces/"+token, nil)
	if err != nil { return nil, err }
	var result Message
	return &result, json.Unmarshal(data, &result)
}

type CostReportsService struct{ client *Client }

func (s *CostReportsService) List(params *ListParams) (*CostReportList, error) {
	data, err := s.client.doRequest("GET", "/cost_reports"+params.toQuery(), nil)
	if err != nil { return nil, err }
	var result CostReportList
	return &result, json.Unmarshal(data, &result)
}

func (s *CostReportsService) Get(token string) (*CostReport, error) {
	data, err := s.client.doRequest("GET", "/cost_reports/"+token, nil)
	if err != nil { return nil, err }
	var result CostReport
	return &result, json.Unmarshal(data, &result)
}

func (s *CostReportsService) Create(body map[string]interface{}) (*CostReport, error) {
	data, err := s.client.doRequest("POST", "/cost_reports", body)
	if err != nil { return nil, err }
	var result CostReport
	return &result, json.Unmarshal(data, &result)
}

func (s *CostReportsService) Delete(token string) (*Message, error) {
	data, err := s.client.doRequest("DELETE", "/cost_reports/"+token, nil)
	if err != nil { return nil, err }
	var result Message
	return &result, json.Unmarshal(data, &result)
}

type FoldersService struct{ client *Client }

func (s *FoldersService) List(params *ListParams) (*FolderList, error) {
	data, err := s.client.doRequest("GET", "/folders"+params.toQuery(), nil)
	if err != nil { return nil, err }
	var result FolderList
	return &result, json.Unmarshal(data, &result)
}

func (s *FoldersService) Create(body map[string]interface{}) (*Folder, error) {
	data, err := s.client.doRequest("POST", "/folders", body)
	if err != nil { return nil, err }
	var result Folder
	return &result, json.Unmarshal(data, &result)
}

func (s *FoldersService) Delete(token string) (*Message, error) {
	data, err := s.client.doRequest("DELETE", "/folders/"+token, nil)
	if err != nil { return nil, err }
	var result Message
	return &result, json.Unmarshal(data, &result)
}

type SegmentsService struct{ client *Client }

func (s *SegmentsService) List(params *ListParams) (*SegmentList, error) {
	data, err := s.client.doRequest("GET", "/segments"+params.toQuery(), nil)
	if err != nil { return nil, err }
	var result SegmentList
	return &result, json.Unmarshal(data, &result)
}

func (s *SegmentsService) Create(body map[string]interface{}) (*Segment, error) {
	data, err := s.client.doRequest("POST", "/segments", body)
	if err != nil { return nil, err }
	var result Segment
	return &result, json.Unmarshal(data, &result)
}

func (s *SegmentsService) Delete(token string) (*Message, error) {
	data, err := s.client.doRequest("DELETE", "/segments/"+token, nil)
	if err != nil { return nil, err }
	var result Message
	return &result, json.Unmarshal(data, &result)
}

type TeamsService struct{ client *Client }

func (s *TeamsService) List(params *ListParams) (*TeamList, error) {
	data, err := s.client.doRequest("GET", "/teams"+params.toQuery(), nil)
	if err != nil { return nil, err }
	var result TeamList
	return &result, json.Unmarshal(data, &result)
}

func (s *TeamsService) Create(body map[string]interface{}) (*Team, error) {
	data, err := s.client.doRequest("POST", "/teams", body)
	if err != nil { return nil, err }
	var result Team
	return &result, json.Unmarshal(data, &result)
}

func (s *TeamsService) Delete(token string) (*Message, error) {
	data, err := s.client.doRequest("DELETE", "/teams/"+token, nil)
	if err != nil { return nil, err }
	var result Message
	return &result, json.Unmarshal(data, &result)
}

type VirtualTagsService struct{ client *Client }

func (s *VirtualTagsService) List(params *ListParams) (*VirtualTagList, error) {
	data, err := s.client.doRequest("GET", "/virtual_tags"+params.toQuery(), nil)
	if err != nil { return nil, err }
	var result VirtualTagList
	return &result, json.Unmarshal(data, &result)
}

func (s *VirtualTagsService) Create(body map[string]interface{}) (*VirtualTag, error) {
	data, err := s.client.doRequest("POST", "/virtual_tags", body)
	if err != nil { return nil, err }
	var result VirtualTag
	return &result, json.Unmarshal(data, &result)
}

func (s *VirtualTagsService) Delete(token string) (*Message, error) {
	data, err := s.client.doRequest("DELETE", "/virtual_tags/"+token, nil)
	if err != nil { return nil, err }
	var result Message
	return &result, json.Unmarshal(data, &result)
}

type APITokensService struct{ client *Client }

func (s *APITokensService) List() (*struct {
	APITokens []APITokenResponse `json:"api_tokens"`
}, error) {
	data, err := s.client.doRequest("GET", "/api_tokens", nil)
	if err != nil { return nil, err }
	var result struct {
		APITokens []APITokenResponse `json:"api_tokens"`
	}
	return &result, json.Unmarshal(data, &result)
}

func (s *APITokensService) Create(name, scopes string) (*APITokenCreated, error) {
	data, err := s.client.doRequest("POST", "/api_tokens", map[string]interface{}{
		"name": name, "scopes": scopes,
	})
	if err != nil { return nil, err }
	var result APITokenCreated
	return &result, json.Unmarshal(data, &result)
}

func (s *APITokensService) Revoke(tokenPrefix string) (*Message, error) {
	data, err := s.client.doRequest("DELETE", "/api_tokens/"+tokenPrefix, nil)
	if err != nil { return nil, err }
	var result Message
	return &result, json.Unmarshal(data, &result)
}
