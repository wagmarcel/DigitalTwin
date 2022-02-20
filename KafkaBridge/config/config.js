
module.exports ={
	"kafka": {
		"brokers": ["my-cluster-kafka-bootstrap:9092"],
	},
	"alerta": {
		"topic": "iff.alerts",
		"hostname": "alerta",
		"port": "8080",
		"protocol": "http:",
		"tokenRefreshInterval": 60,
		"accessKey": "t9ODS70LWNqEEo_0f2lDN7bnTAfiW0ucciAthrHj"
	},
	"logger": {
		"loglevel": "debug"
	},
	"keycloak": {
		"ngsildUpdatesAuthService": {
			"port": 80,
			"auth-server-url":  "http://keycloak.local/auth",
			"realm": "scorpio",
			"clientId": "ngsildUpdates",
			"resource": "ngsildUpdates",
			"secret": "g5mazZJStwUpJGyochsHQC3kS7gnwycA",
			"bearer-only": true,
			"verify-token-audience": false,
			"ssl-required": false
		}
	},
	"ngsildUpdates": {
		"topic": "iff.ngsildUpdates",
		"refreshIntervalInSeconds": 60
	},        
	"ngsildServer": {
		"host": "ngsild.local",
		"port": 80
	},
	"debeziumBridge": {
		"topic": "iff.ngsild.public.entity",
		"entityTopicPrefix": "iff.ngsild.entities",
		"attributesTopic": "iff.ngsild.attributes",
		"rdfSources": ['../config/knowledge.ttl']
	}
}
