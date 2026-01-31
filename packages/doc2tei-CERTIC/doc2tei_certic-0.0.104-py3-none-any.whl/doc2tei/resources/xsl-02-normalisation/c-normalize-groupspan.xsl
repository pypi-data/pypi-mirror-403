<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
  xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
  xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"
  xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" 
  xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0" 
  xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0" 
  xmlns:math="http://www.w3.org/1998/Math/MathML" 
  xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0" 
  xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0" 
  xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0" 
  xmlns:ooo="http://openoffice.org/2004/office" 
  xmlns:ooow="http://openoffice.org/2004/writer" 
  xmlns:oooc="http://openoffice.org/2004/calc" 
  xmlns:dom="http://www.w3.org/2001/xml-events" 
  xmlns:xforms="http://www.w3.org/2002/xforms" 
  xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
  xmlns:rpt="http://openoffice.org/2005/report" 
  xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2" 
  xmlns:xhtml="http://www.w3.org/1999/xhtml" 
  xmlns:grddl="http://www.w3.org/2003/g/data-view#" 
  xmlns:officeooo="http://openoffice.org/2009/office" 
  xmlns:tableooo="http://openoffice.org/2009/table" 
  xmlns:drawooo="http://openoffice.org/2010/draw" 
  xmlns:calcext="urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0" 
  xmlns:loext="urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0" 
  xmlns:field="urn:openoffice:names:experimental:ooo-ms-interop:xmlns:field:1.0" 
  xmlns:formx="urn:openoffice:names:experimental:ooxml-odf-interop:xmlns:form:1.0" 
  xmlns:css3t="http://www.w3.org/TR/css3-text/"		
  exclude-result-prefixes="">
    
<xsl:output method="xml" encoding="UTF-8" indent="no"/>

<!-- ajouter LICENCE -->
<!-- voir README.md pour la description des traitements XSL -->

<xsl:template match="@*|node()">
  <xsl:copy>
    <xsl:apply-templates select="@*|node()" />
  </xsl:copy>
</xsl:template>

<xsl:template match="text:*[text:span/@text:style-name]">
  <xsl:copy>
    <xsl:apply-templates select="@*" />
    <xsl:for-each-group select="node()" group-adjacent="
       if (self::*[not(child::text:tab)]/@text:style-name) then
           concat( namespace-uri(), '|', local-name(), '|', @text:style-name)
         else
           ''">
      <xsl:choose>
        <xsl:when test="current-grouping-key()" >
          <xsl:for-each select="current-group()[1]">
            <xsl:copy>
              <xsl:apply-templates select="@* | current-group()/node()" />
            </xsl:copy>
          </xsl:for-each>
        </xsl:when>
        <xsl:otherwise>
         <xsl:apply-templates select="current-group()" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:for-each-group>
  </xsl:copy>
</xsl:template>
    
<!-- les text:span contenant des tabulations sont exclus du template précédent (ligne 58) et sont traités ici : on exfiltre la tabulation du text:span qui la contient -->
<xsl:template match="text:span[child::text:tab]">
    <xsl:if test="text:tab/preceding-sibling::node() != ''">
        <text:span><xsl:copy-of select="@*"/><xsl:apply-templates select="text:tab/preceding-sibling::node()"/></text:span>
    </xsl:if>
    <text:tab/>
    <xsl:if test="text:tab/following-sibling::node() != ''">
        <text:span><xsl:copy-of select="@*"/><xsl:apply-templates select="text:tab/following-sibling::node()"/></text:span>
    </xsl:if>
</xsl:template>

</xsl:stylesheet>