import React, { useState, useEffect } from 'react';
import { Search, Info, X } from 'lucide-react';

const MythExplorer = () => {
  const [jsonData, setJsonData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [entityMap, setEntityMap] = useState({});
  const [relationshipData, setRelationshipData] = useState({});

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const response = await window.fs.readFile('pm010_first_words_merged.jsonld');
        const text = new TextDecoder().decode(response);
        const data = JSON.parse(text);
        setJsonData(data);

        // Build entity map for quick reference
        const entityMapTemp = {};
        data.assertions.forEach(a => {
          if (a.entity && a.entity["@id"] && a.entity.name) {
            entityMapTemp[a.entity["@id"]] = {
              name: a.entity.name,
              type: a.entity.type
            };
          }
        });
        setEntityMap(entityMapTemp);

        // Process relationships
        processRelationships(data, entityMapTemp);

      } catch (error) {
        console.error('Error loading data:', error);
        setError('Failed to load the myth data. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const processRelationships = (data, entityMapTemp) => {
    const relationships = {};

    // Process all entities
    data.assertions.forEach(a => {
      if (a.entity && a.entity.name) {
        const entityName = a.entity.name;
        const entityId = a.entity["@id"];

        if (!relationships[entityName]) {
          relationships[entityName] = {
            id: entityId,
            type: a.entity.type,
            events: [],
            relationsAsSubject: [],
            relationsAsObject: []
          };
        }
      }
    });

    // Process events
    data.assertions.forEach(a => {
      if (a.event) {
        const event = a.event;
        const agentId = event.agent;
        const patientId = event.patient;

        // Add event to agent's record
        if (agentId && entityMapTemp[agentId]) {
          const agentName = entityMapTemp[agentId].name;
          if (relationships[agentName]) {
            relationships[agentName].events.push({
              id: event["@id"],
              type: event.type,
              name: event.name,
              role: 'agent',
              targetId: patientId,
              targetName: patientId && entityMapTemp[patientId] ?
                entityMapTemp[patientId].name :
                (patientId && patientId.startsWith('myth:') ?
                  patientId.replace('myth:', '') : patientId)
            });
          }
        }

        // Add event to patient's record if patient is a known entity
        if (patientId && entityMapTemp[patientId]) {
          const patientName = entityMapTemp[patientId].name;
          if (relationships[patientName]) {
            relationships[patientName].events.push({
              id: event["@id"],
              type: event.type,
              name: event.name,
              role: 'patient',
              targetId: agentId,
              targetName: agentId && entityMapTemp[agentId] ?
                entityMapTemp[agentId].name : agentId
            });
          }
        }
      }
    });

    // Process relations
    data.assertions.forEach(a => {
      if (a.relation) {
        const relation = a.relation;
        const subjectId = relation.subject;
        const objectId = relation.object;

        // Add relation to subject's record
        if (subjectId && entityMapTemp[subjectId]) {
          const subjectName = entityMapTemp[subjectId].name;
          if (relationships[subjectName]) {
            relationships[subjectName].relationsAsSubject.push({
              id: relation["@id"],
              type: relation.type,
              targetId: objectId,
              targetName: objectId && entityMapTemp[objectId] ?
                entityMapTemp[objectId].name :
                (objectId && objectId.startsWith('myth:') ?
                  objectId.replace('myth:', '') : objectId)
            });
          }
        }

        // Add relation to object's record if object is a known entity
        if (objectId && entityMapTemp[objectId]) {
          const objectName = entityMapTemp[objectId].name;
          if (relationships[objectName]) {
            relationships[objectName].relationsAsObject.push({
              id: relation["@id"],
              type: relation.type,
              targetId: subjectId,
              targetName: subjectId && entityMapTemp[subjectId] ?
                entityMapTemp[subjectId].name : subjectId
            });
          }
        }
      }
    });

    setRelationshipData(relationships);
  };

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleSelectEntity = (entityName) => {
    setSelectedEntity(entityName);
  };

  const filteredEntities = Object.keys(relationshipData)
    .filter(name => name.toLowerCase().includes(searchTerm.toLowerCase()))
    .sort();

  if (loading) return <div className="flex items-center justify-center h-64">Loading myth data...</div>;
  if (error) return <div className="text-red-500 p-4">{error}</div>;

  return (
    <div className="flex flex-col h-full bg-gray-50 rounded-lg shadow overflow-hidden">
      <div className="p-4 bg-indigo-700 text-white">
        <h1 className="text-xl font-bold">Myth Entity Explorer</h1>
        <p className="text-sm opacity-80">Explore entities from the merged JSON-LD</p>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Entity List Panel */}
        <div className="w-1/3 border-r border-gray-200 bg-white overflow-hidden flex flex-col">
          <div className="p-3 border-b border-gray-200">
            <div className="relative">
              <input
                type="text"
                placeholder="Search entities..."
                value={searchTerm}
                onChange={handleSearch}
                className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-400" />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto">
            {filteredEntities.length === 0 ? (
              <div className="p-4 text-center text-gray-500">No entities found</div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {filteredEntities.map(entityName => (
                  <li key={entityName}>
                    <button
                      className={`w-full text-left px-4 py-3 hover:bg-gray-100 focus:outline-none ${
                        selectedEntity === entityName ? 'bg-indigo-50 border-l-4 border-indigo-500' : ''
                      }`}
                      onClick={() => handleSelectEntity(entityName)}
                    >
                      <div className="font-medium">{entityName}</div>
                      <div className="text-sm text-gray-500">
                        Type: {relationshipData[entityName]?.type?.replace('myth:', '')}
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Entity Detail Panel */}
        <div className="w-2/3 bg-white overflow-y-auto">
          {selectedEntity ? (
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">{selectedEntity}</h2>
                <button
                  className="text-gray-400 hover:text-gray-600"
                  onClick={() => setSelectedEntity(null)}
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="mb-4 p-3 bg-gray-50 rounded-md">
                <div className="text-sm text-gray-700">
                  <strong>ID:</strong> {relationshipData[selectedEntity]?.id}
                </div>
                <div className="text-sm text-gray-700">
                  <strong>Type:</strong> {relationshipData[selectedEntity]?.type?.replace('myth:', '')}
                </div>
              </div>

              {/* Events where entity is the agent */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="mr-2">Actions</span>
                  <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                    {relationshipData[selectedEntity]?.events.filter(e => e.role === 'agent').length}
                  </span>
                </h3>

                {relationshipData[selectedEntity]?.events.filter(e => e.role === 'agent').length > 0 ? (
                  <ul className="space-y-2">
                    {relationshipData[selectedEntity]?.events
                      .filter(e => e.role === 'agent')
                      .map(event => (
                        <li key={event.id} className="p-3 border border-gray-200 rounded-md hover:bg-gray-50">
                          <div className="font-medium">
                            {event.type?.replace('myth:', '')}
                            {event.name && ` - ${event.name}`}
                          </div>
                          {event.targetName && (
                            <div className="text-sm">
                              Target: <span className="text-indigo-600">{event.targetName}</span>
                            </div>
                          )}
                        </li>
                      ))}
                  </ul>
                ) : (
                  <p className="text-gray-500 italic">No actions found</p>
                )}
              </div>

              {/* Events where entity is the patient */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="mr-2">Affected By</span>
                  <span className="text-xs px-2 py-1 bg-purple-100 text-purple-800 rounded-full">
                    {relationshipData[selectedEntity]?.events.filter(e => e.role === 'patient').length}
                  </span>
                </h3>

                {relationshipData[selectedEntity]?.events.filter(e => e.role === 'patient').length > 0 ? (
                  <ul className="space-y-2">
                    {relationshipData[selectedEntity]?.events
                      .filter(e => e.role === 'patient')
                      .map(event => (
                        <li key={event.id} className="p-3 border border-gray-200 rounded-md hover:bg-gray-50">
                          <div className="font-medium">
                            {event.type?.replace('myth:', '')}
                            {event.name && ` - ${event.name}`}
                          </div>
                          {event.targetName && (
                            <div className="text-sm">
                              Agent: <span className="text-indigo-600">{event.targetName}</span>
                            </div>
                          )}
                        </li>
                      ))}
                  </ul>
                ) : (
                  <p className="text-gray-500 italic">No effects found</p>
                )}
              </div>

              {/* Relations where entity is the subject */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="mr-2">Relations (As Subject)</span>
                  <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">
                    {relationshipData[selectedEntity]?.relationsAsSubject.length}
                  </span>
                </h3>

                {relationshipData[selectedEntity]?.relationsAsSubject.length > 0 ? (
                  <ul className="space-y-2">
                    {relationshipData[selectedEntity]?.relationsAsSubject.map(relation => (
                      <li key={relation.id} className="p-3 border border-gray-200 rounded-md hover:bg-gray-50">
                        <div className="font-medium">
                          {relation.type?.replace('myth:', '')}
                        </div>
                        {relation.targetName && (
                          <div className="text-sm">
                            Object: <span className="text-indigo-600">{relation.targetName}</span>
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500 italic">No outgoing relations found</p>
                )}
              </div>

              {/* Relations where entity is the object */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="mr-2">Relations (As Object)</span>
                  <span className="text-xs px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full">
                    {relationshipData[selectedEntity]?.relationsAsObject.length}
                  </span>
                </h3>

                {relationshipData[selectedEntity]?.relationsAsObject.length > 0 ? (
                  <ul className="space-y-2">
                    {relationshipData[selectedEntity]?.relationsAsObject.map(relation => (
                      <li key={relation.id} className="p-3 border border-gray-200 rounded-md hover:bg-gray-50">
                        <div className="font-medium">
                          {relation.type?.replace('myth:', '')}
                        </div>
                        {relation.targetName && (
                          <div className="text-sm">
                            Subject: <span className="text-indigo-600">{relation.targetName}</span>
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500 italic">No incoming relations found</p>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">
              <div className="text-center p-6">
                <Info className="h-12 w-12 mx-auto mb-4" />
                <p>Select an entity from the list to view details</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MythExplorer;